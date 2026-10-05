# FitBuddy – AI Fitness Plan Generator using Gemini Models

FitBuddy is a web application that generates personalised **weekly workout plans**, **calorie and macro
targets**, **meal ideas** and **recovery tips** from a user's body stats, goal, schedule, equipment and diet.
It is built with **Python (FastAPI)**, **HTML** (Jinja2 templates) and **CSS** only: no JavaScript is required.
Plans come from **Google Gemini** using structured JSON output.

## Features

- Structured plans from Gemini using a Pydantic response schema (validated before they are shown)
- BMI, BMR, TDEE, calorie target and macros computed server-side (Mifflin-St Jeor) and fed into the prompt
- Automatic fallback to a second Gemini model, plus a friendly error if the AI is unavailable
- **Demo mode**: works without an API key using a rule-based plan generator
- Server-rendered, responsive UI with automatic light/dark theme; print to PDF with Ctrl/Cmd + P
- Form validation that keeps what you typed, per-IP rate limiting, security headers, auto-escaped output
- JSON API (`/api/plan`), tests (pytest), Dockerfile and docker-compose

## Project structure

```
fitbuddy/
├── app/
│   ├── main.py               # App factory, middleware, error handlers
│   ├── config.py             # Settings from .env
│   ├── schemas.py            # Request/response + Gemini schema models
│   ├── routers/
│   │   ├── pages.py          # HTML routes: GET /, POST /generate
│   │   └── api.py            # JSON routes: /api/health, /api/plan
│   ├── services/
│   │   ├── gemini_service.py # Gemini calls, fallback, parsing
│   │   ├── prompts.py        # System instruction and prompt builder
│   │   └── demo_plan.py      # Offline rule-based plan generator
│   ├── utils/health.py       # BMI / BMR / TDEE / macros
│   ├── templates/            # base.html, index.html, result.html
│   └── static/css/style.css  # All styling
├── tests/                    # pytest suite
├── run.py                    # Local launcher
├── requirements.txt / requirements-dev.txt
├── .env.example
├── Dockerfile / docker-compose.yml
└── README.md
```

## Quick start

```bash
cd fitbuddy
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # Windows: copy .env.example .env
# Edit .env and set GEMINI_API_KEY (free key: https://aistudio.google.com/app/apikey)

python run.py
```

Open <http://127.0.0.1:8000>. Interactive API docs: <http://127.0.0.1:8000/docs>.

If `GEMINI_API_KEY` is empty the app runs in **demo mode** (a badge in the header shows this).

## API

| Method | Path          | Description                                  |
|--------|---------------|----------------------------------------------|
| GET    | `/`           | Plan form                                    |
| POST   | `/generate`   | Form submit → rendered plan page             |
| GET    | `/api/health` | Status, version, demo mode flag              |
| POST   | `/api/plan`   | JSON profile → metrics + weekly plan         |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/plan -H "Content-Type: application/json" -d '{
  "age": 28, "gender": "male", "height_cm": 175, "weight_kg": 72,
  "goal": "muscle_gain", "activity_level": "moderate", "experience": "intermediate",
  "days_per_week": 4, "session_minutes": 45, "equipment": "gym", "diet": "no_preference"
}'
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Docker

```bash
cp .env.example .env   # add your key
docker compose up --build
```

## Configuration

| Variable                | Default                  | Purpose                          |
|-------------------------|--------------------------|----------------------------------|
| `GEMINI_API_KEY`        | *(empty)*                | Enables real AI plans            |
| `GEMINI_MODEL`          | `gemini-2.5-flash`       | Primary model                    |
| `GEMINI_FALLBACK_MODEL` | `gemini-2.5-flash-lite`  | Used if the primary fails        |
| `GEMINI_TIMEOUT_SECONDS`| `60`                     | Per-request timeout              |
| `RATE_LIMIT_PER_MINUTE` | `20`                     | Per-IP limit on plan/chat calls  |
| `CORS_ORIGINS`          | `*`                      | Comma-separated allowed origins  |

Model names change over time; if a model is retired, set `GEMINI_MODEL` to a current one.

## Disclaimer

FitBuddy provides general fitness information, not medical advice. Consult a doctor before starting any
exercise or nutrition programme, especially with injuries, medical conditions or pregnancy, or if under 18.
