from flask import Flask, request, render_template
from flask_cors import cross_origin
import pickle
import pandas as pd

app = Flask(__name__)
model = None
model_load_error = None
flight_data = None
flight_data_loaded = False


def get_model():
    global model, model_load_error
    if model is not None:
        return model
    if model_load_error is not None:
        raise model_load_error
    try:
        with open("flight_rf.pkl", "rb") as model_file:
            model = pickle.load(model_file)
    except Exception as exc:
        model_load_error = exc
        raise
    return model


def get_flight_data():
    global flight_data, flight_data_loaded
    if flight_data_loaded:
        return flight_data
    flight_data_loaded = True
    try:
        flight_data = pd.read_excel("Data_Train.xlsx")
        flight_data.dropna(inplace=True)
    except Exception as exc:
        print(f"Dashboard data could not be loaded: {exc}", flush=True)
        flight_data = None
    return flight_data


def normalize_duration(duration_text):
    if not isinstance(duration_text, str):
        return 0
    text = duration_text.strip()
    if "h" not in text and "m" in text:
        text = f"0h {text}"
    if "m" not in text and "h" in text:
        text = f"{text} 0m"
    parts = text.split()
    hours = 0
    mins = 0
    for part in parts:
        if part.endswith("h"):
            hours = int(part[:-1])
        elif part.endswith("m"):
            mins = int(part[:-1])
    return hours * 60 + mins


def parse_datetime_input(value):
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    dt = pd.to_datetime(value, format="%Y-%m-%dT%H:%M", errors="coerce")
    if pd.isna(dt):
        try:
            dt = pd.to_datetime(value, errors="coerce")
        except Exception:
            dt = pd.NaT
    return None if pd.isna(dt) else dt


def get_dashboard_data():
    source_data = get_flight_data()
    if source_data is None:
        return {}

    df = source_data.copy()
    if "Total_Stops" in df.columns:
        df["Total_Stops"] = df["Total_Stops"].replace({"non-stop": "0 stop", "non stop": "0 stop"})

    if "Date_of_Journey" in df.columns:
        df["Journey_month"] = pd.to_datetime(df["Date_of_Journey"], format="%d/%m/%Y", errors="coerce").dt.month

    if "Duration" in df.columns:
        duration_minutes = df["Duration"].apply(normalize_duration).tolist()
        avg_duration = int(sum(duration_minutes) / len(duration_minutes)) if duration_minutes else 0
    else:
        avg_duration = 0

    total_flights = int(df.shape[0])
    avg_price = int(df["Price"].mean()) if "Price" in df.columns else 0
    min_price = int(df["Price"].min()) if "Price" in df.columns else 0
    max_price = int(df["Price"].max()) if "Price" in df.columns else 0

    airline_counts = df["Airline"].value_counts().head(6).to_dict() if "Airline" in df.columns else {}
    stops_counts = df["Total_Stops"].value_counts().to_dict() if "Total_Stops" in df.columns else {}
    route_counts = df["Route"].value_counts().head(5).to_dict() if "Route" in df.columns else {}

    monthly_avg = []
    if "Journey_month" in df.columns and "Price" in df.columns:
        monthly_avg = (
            df.groupby("Journey_month")["Price"]
            .mean()
            .reindex(range(1, 13), fill_value=0)
            .round(0)
            .astype(int)
            .tolist()
        )
    else:
        monthly_avg = [0] * 12

    price_labels = ["0-5k", "5-10k", "10-15k", "15-20k", "20-25k", "25k+"]
    if "Price" in df.columns:
        price_bin_counts = (
            pd.cut(df["Price"], bins=[0, 5000, 10000, 15000, 20000, 25000, float("inf")], labels=price_labels, include_lowest=True)
            .value_counts()
            .reindex(price_labels, fill_value=0)
            .astype(int)
            .tolist()
        )
    else:
        price_bin_counts = [0] * len(price_labels)

    return {
        "total_flights": total_flights,
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "avg_duration": avg_duration,
        "airline_labels": list(airline_counts.keys()),
        "airline_counts": list(airline_counts.values()),
        "stops_labels": list(stops_counts.keys()),
        "stops_counts": list(stops_counts.values()),
        "route_labels": list(route_counts.keys()),
        "route_counts": list(route_counts.values()),
        "monthly_avg": monthly_avg,
        "price_bins_labels": price_labels,
        "price_bin_counts": price_bin_counts,
    }





@app.route("/")
@cross_origin()
def home():

    dashboard = get_dashboard_data()
    return render_template("home.html", dashboard=dashboard, prediction_text="")




@app.route("/predict", methods = ["GET", "POST"])
@cross_origin()
def predict():
    if request.method == "POST":

        # Date_of_Journey
        date_dep = request.form["Dep_Time"]
        dep_dt = parse_datetime_input(date_dep)
        date_arr = request.form["Arrival_Time"]
        arr_dt = parse_datetime_input(date_arr)

        if dep_dt is None or arr_dt is None:
            dashboard = get_dashboard_data()
            return render_template(
                'home.html',
                dashboard=dashboard,
                prediction_text="Invalid departure or arrival date/time. Please use the form input and enter a valid date/time.",
            )

        if arr_dt <= dep_dt:
            dashboard = get_dashboard_data()
            return render_template(
                'home.html',
                dashboard=dashboard,
                prediction_text="Arrival must be after departure. Please enter valid departure and arrival times.",
            )

        Journey_day = int(dep_dt.day)
        Journey_month = int(dep_dt.month)

        # Departure
        Dep_hour = int(dep_dt.hour)
        Dep_min = int(dep_dt.minute)

        # Arrival
        Arrival_hour = int(arr_dt.hour)
        Arrival_min = int(arr_dt.minute)

        # Duration
        duration_delta = arr_dt - dep_dt
        total_minutes = int(duration_delta.total_seconds() // 60)
        dur_hour = total_minutes // 60
        dur_min = total_minutes % 60

        # Total Stops
        Total_stops = int(request.form["stops"])
        # print(Total_stops)

        # Airline
        # AIR ASIA = 0 (not in column)
        airline=request.form['airline']
        if(airline=='Jet Airways'):
            Jet_Airways = 1
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0 

        elif (airline=='IndiGo'):
            Jet_Airways = 0
            IndiGo = 1
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0 

        elif (airline=='Air India'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 1
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0 
            
        elif (airline=='Multiple carriers'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 1
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0 
            
        elif (airline=='SpiceJet'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 1
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0 
            
        elif (airline=='Vistara'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 1
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif (airline=='GoAir'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 1
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif (airline=='Multiple carriers Premium economy'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 1
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        elif (airline=='Jet Airways Business'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 1
            Vistara_Premium_economy = 0
            Trujet = 0

        elif (airline=='Vistara Premium economy'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 1
            Trujet = 0
            
        elif (airline=='Trujet'):
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 1

        else:
            Jet_Airways = 0
            IndiGo = 0
            Air_India = 0
            Multiple_carriers = 0
            SpiceJet = 0
            Vistara = 0
            GoAir = 0
            Multiple_carriers_Premium_economy = 0
            Jet_Airways_Business = 0
            Vistara_Premium_economy = 0
            Trujet = 0

        # print(Jet_Airways,
        #     IndiGo,
        #     Air_India,
        #     Multiple_carriers,
        #     SpiceJet,
        #     Vistara,
        #     GoAir,
        #     Multiple_carriers_Premium_economy,
        #     Jet_Airways_Business,
        #     Vistara_Premium_economy,
        #     Trujet)

        # Source
        # Banglore = 0 (not in column)
        Source = request.form["Source"]
        if (Source == 'Delhi'):
            s_Delhi = 1
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 0

        elif (Source == 'Kolkata'):
            s_Delhi = 0
            s_Kolkata = 1
            s_Mumbai = 0
            s_Chennai = 0

        elif (Source == 'Mumbai'):
            s_Delhi = 0
            s_Kolkata = 0
            s_Mumbai = 1
            s_Chennai = 0

        elif (Source == 'Chennai'):
            s_Delhi = 0
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 1

        else:
            s_Delhi = 0
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 0

        # print(s_Delhi,
        #     s_Kolkata,
        #     s_Mumbai,
        #     s_Chennai)

        # Destination
        # Banglore = 0 (not in column)
        Source = request.form["Destination"]
        if (Source == 'Cochin'):
            d_Cochin = 1
            d_Delhi = 0
            d_New_Delhi = 0
            d_Hyderabad = 0
            d_Kolkata = 0
        
        elif (Source == 'Delhi'):
            d_Cochin = 0
            d_Delhi = 1
            d_New_Delhi = 0
            d_Hyderabad = 0
            d_Kolkata = 0

        elif (Source == 'New_Delhi'):
            d_Cochin = 0
            d_Delhi = 0
            d_New_Delhi = 1
            d_Hyderabad = 0
            d_Kolkata = 0

        elif (Source == 'Hyderabad'):
            d_Cochin = 0
            d_Delhi = 0
            d_New_Delhi = 0
            d_Hyderabad = 1
            d_Kolkata = 0

        elif (Source == 'Kolkata'):
            d_Cochin = 0
            d_Delhi = 0
            d_New_Delhi = 0
            d_Hyderabad = 0
            d_Kolkata = 1

        else:
            d_Cochin = 0
            d_Delhi = 0
            d_New_Delhi = 0
            d_Hyderabad = 0
            d_Kolkata = 0

        # print(
        #     d_Cochin,
        #     d_Delhi,
        #     d_New_Delhi,
        #     d_Hyderabad,
        #     d_Kolkata
        # )
        

    #     ['Total_Stops', 'Journey_day', 'Journey_month', 'Dep_hour',
    #    'Dep_min', 'Arrival_hour', 'Arrival_min', 'Duration_hours',
    #    'Duration_mins', 'Airline_Air India', 'Airline_GoAir', 'Airline_IndiGo',
    #    'Airline_Jet Airways', 'Airline_Jet Airways Business',
    #    'Airline_Multiple carriers',
    #    'Airline_Multiple carriers Premium economy', 'Airline_SpiceJet',
    #    'Airline_Trujet', 'Airline_Vistara', 'Airline_Vistara Premium economy',
    #    'Source_Chennai', 'Source_Delhi', 'Source_Kolkata', 'Source_Mumbai',
    #    'Destination_Cochin', 'Destination_Delhi', 'Destination_Hyderabad',
    #    'Destination_Kolkata', 'Destination_New Delhi']
        
        try:
            prediction = get_model().predict([[
                Total_stops,
                Journey_day,
                Journey_month,
                Dep_hour,
                Dep_min,
                Arrival_hour,
                Arrival_min,
                dur_hour,
                dur_min,
                Air_India,
                GoAir,
                IndiGo,
                Jet_Airways,
                Jet_Airways_Business,
                Multiple_carriers,
                Multiple_carriers_Premium_economy,
                SpiceJet,
                Trujet,
                Vistara,
                Vistara_Premium_economy,
                s_Chennai,
                s_Delhi,
                s_Kolkata,
                s_Mumbai,
                d_Cochin,
                d_Delhi,
                d_Hyderabad,
                d_Kolkata,
                d_New_Delhi
            ]])
        except Exception as exc:
            dashboard = get_dashboard_data()
            return render_template(
                "home.html",
                prediction_text=f"Prediction model could not be loaded: {exc}",
                dashboard=dashboard,
            )

        output=round(prediction[0],2)

        dashboard = get_dashboard_data()
        return render_template('home.html', prediction_text="Your Flight price is Rs. {}".format(output), dashboard=dashboard)


    dashboard = get_dashboard_data()
    return render_template("home.html", dashboard=dashboard, prediction_text="")




if __name__ == "__main__":
    app.run(debug=True)
