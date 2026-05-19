Steps to run Flight Fare App - on Windows
Prerequisites: Python 3.9 (ensure Python is added to PATH) + Git Client

Open GIT CMD >> navigate to working directory >> Clone this Github Repo (or download project files from GitHub directly)

git clone    git@github.com:itismeriya/flight_price_prediction_model.git
Open Windows Powershell >> navigate to new working directory (cloned repo folder)

Run Project in Flask (Using PIP + Virtualenv)

  pip install virtualenv                  # install virtual environment        
  virtualenv ENV                          # create virtual environment by the name ENV
  .\ENV\Scripts\activate                  # activate ENV
  pip install -r .\requirements.txt       # install project dependencies
  python app.py                           # run the project
  deactivate                              # close virtual environment once done
