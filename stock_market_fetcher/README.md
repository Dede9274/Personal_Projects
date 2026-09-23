# PulseStock

PulseStock serves a small modular frontend and a Flask API from the same local
server. Finnhub and Groq credentials are read only by Flask; they are never
included in browser code or browser requests.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FINNHUB_API_KEY="your-finnhub-key"
export GROQ_API_KEY="your-groq-key"
python3 finnhub_proxy.py
```

Open <http://localhost:5050>.

`GROQ_MODEL` can optionally override the default `openai/gpt-oss-20b` model.

## Screenshots

### Dashboard

![PulseStock dashboard setup and ticker selection](fotos/Dashboard.png)

### AI sentiment results

![PulseStock news feed with bullish, bearish, and neutral analysis](fotos/Results.png)

## Tests

Install the Python development dependency and run both suites:

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests
npm test
```

The backend suite mocks Finnhub and Groq, so tests never call external APIs
or require real credentials. The frontend suite uses Node's built-in test runner
and has no npm dependencies.

## API

- `GET /api/health` reports whether both integrations are configured.
- `GET /api/news/<ticker>` fetches recent company news from Finnhub.
- `POST /api/analyse-news` accepts `{ "articles": [...] }` and returns the
  articles enriched with `sentiment` and `reason` fields.

## Project structure

```text
frontend/
├── index.html
├── css/
│   └── styles.css
└── js/
    ├── api.js
    ├── app.js
    ├── state.js
    └── ui.js
tests/
└── test_api.py
```
