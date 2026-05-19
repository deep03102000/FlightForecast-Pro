# FlightForecast Pro

Lightweight Flask app that displays flight fare analytics and provides a fare prediction form powered by a trained Random Forest model.

## Features

- Dashboard metrics and charts (Chart.js)
- Predict fare from form inputs (`/predict`)
- Tailwind CSS-based UI (via CDN)

## Prerequisites

- Python 3.8
- Git (to clone/push repository)

## Quick start (local)

1. Clone the repo:

```bash
git clone <your-repo-url>
cd flight_price_prediction_model-main
```

2. Create and activate a virtual environment:

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies and run:

```bash
pip install -r requirements.txt
python app.py
```

The app will run on `http://127.0.0.1:5000` by default.

## Run in production (recommended)

This project includes a `Procfile` and `gunicorn` in `requirements.txt`. Start with:

```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

When deploying to a PaaS (Render, Heroku, etc.) use the start command above. PaaS platforms expose the port via the `PORT` env var, so the `Procfile` already contains:

```
web: gunicorn app:app
```

## Deploying (recommended: Render)

1. Push your repo to GitHub.
2. Create a new Web Service on Render and connect your GitHub repo.
3. Runtime: this repo includes `.python-version` with `3.8.18` so the pinned ML dependencies install cleanly.
4. Build command: `pip install -r requirements.txt` (Render auto-installs by default).
5. Start command: `gunicorn --bind 0.0.0.0:$PORT app:app`.
6. Add any required environment variables under the service settings.

Notes on model and data:

- `flight_rf.pkl` (trained model) and `Data_Train.xlsx` (training data) are required for the deployed app and are explicitly allowed in `.gitignore`.
- `Test_set.xlsx` remains ignored because the Flask app does not need it at runtime.

## Project structure

- `app.py` - Flask app and prediction endpoint
- `templates/home.html` - main UI
- `static/` - images and static assets
- `flight_rf.pkl` - trained model (required at runtime)
- `Data_Train.xlsx` - dataset used for dashboard generation
- `requirements.txt`, `Procfile`, `README.md`

## Troubleshooting

- If you see pandas `to_datetime` errors, ensure the installed pandas version matches `requirements.txt` or update parsing code.
- If `flight_rf.pkl` is missing on deploy, app will crash on import. Make sure it is committed or provided by your host before starting the app.

## Next steps I can help with

- Create a GitHub repo and push the project (you can provide credentials/token).
- Configure a Render service and deploy the app.
- Move the model to cloud storage and update `app.py` to fetch it at startup.

---

If you'd like, I can push this repository to GitHub and set up Render for you — tell me which option you prefer and provide the GitHub repo URL or a personal access token (I will guide you how to paste it securely).
