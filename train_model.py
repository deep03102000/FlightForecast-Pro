import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Load training data from the project root
train_data = pd.read_excel("Data_Train.xlsx")
train_data.dropna(inplace=True)

# Date features
train_data["Journey_day"] = pd.to_datetime(train_data["Date_of_Journey"], format="%d/%m/%Y").dt.day
train_data["Journey_month"] = pd.to_datetime(train_data["Date_of_Journey"], format="%d/%m/%Y").dt.month
train_data.drop(["Date_of_Journey"], axis=1, inplace=True)

# Departure features
train_data["Dep_hour"] = pd.to_datetime(train_data["Dep_Time"]).dt.hour
train_data["Dep_min"] = pd.to_datetime(train_data["Dep_Time"]).dt.minute
train_data.drop(["Dep_Time"], axis=1, inplace=True)

# Arrival features
train_data["Arrival_hour"] = pd.to_datetime(train_data["Arrival_Time"]).dt.hour
train_data["Arrival_min"] = pd.to_datetime(train_data["Arrival_Time"]).dt.minute
train_data.drop(["Arrival_Time"], axis=1, inplace=True)

# Duration features
duration = list(train_data["Duration"])
for i in range(len(duration)):
    if len(duration[i].split()) != 2:
        if "h" in duration[i]:
            duration[i] = duration[i].strip() + " 0m"
        else:
            duration[i] = "0h " + duration[i]

train_data["Duration_hours"] = [int(x.split("h")[0]) for x in duration]
train_data["Duration_mins"] = [int(x.split("m")[0].split()[-1]) for x in duration]
train_data.drop(["Duration"], axis=1, inplace=True)

# Encode Total_Stops as integer
train_data["Total_Stops"] = (
    train_data["Total_Stops"]
    .replace({"non-stop": "0 stop", "non stop": "0 stop"})
    .str.extract(r"(\d+)")[0]
    .astype(int)
)

# One-hot encoding for categorical variables
airline_dummies = pd.get_dummies(train_data[["Airline"]], drop_first=True)
source_dummies = pd.get_dummies(train_data[["Source"]], drop_first=True)
destination_dummies = pd.get_dummies(train_data[["Destination"]], drop_first=True)

train_data = pd.concat([train_data, airline_dummies, source_dummies, destination_dummies], axis=1)
train_data.drop(["Airline", "Source", "Destination", "Route", "Additional_Info"], axis=1, inplace=True, errors="ignore")

# Feature order used by app.py
feature_cols = [
    "Total_Stops",
    "Journey_day",
    "Journey_month",
    "Dep_hour",
    "Dep_min",
    "Arrival_hour",
    "Arrival_min",
    "Duration_hours",
    "Duration_mins",
    "Airline_Air India",
    "Airline_GoAir",
    "Airline_IndiGo",
    "Airline_Jet Airways",
    "Airline_Jet Airways Business",
    "Airline_Multiple carriers",
    "Airline_Multiple carriers Premium economy",
    "Airline_SpiceJet",
    "Airline_Trujet",
    "Airline_Vistara",
    "Airline_Vistara Premium economy",
    "Source_Chennai",
    "Source_Delhi",
    "Source_Kolkata",
    "Source_Mumbai",
    "Destination_Cochin",
    "Destination_Delhi",
    "Destination_Hyderabad",
    "Destination_Kolkata",
    "Destination_New Delhi",
]

for col in feature_cols:
    if col not in train_data.columns:
        train_data[col] = 0

X = train_data[feature_cols]
y = train_data["Price"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor()
model.fit(X_train, y_train)

with open("flight_rf.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved to flight_rf.pkl")
