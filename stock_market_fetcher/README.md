# PulseStock

PulseStock is a full-stack stock-news dashboard that collects recent company
headlines and uses an LLM to classify their likely market sentiment. Users can
select or add ticker symbols, fetch current news, and explore bullish, bearish,
or neutral stories with a short explanation for each classification.

The application combines live news from Finnhub with structured sentiment
analysis from Groq. It presents article totals and sentiment statistics, supports
interactive filtering, and links each result back to its original source.

## Features

- Fetches the latest seven days of company news for multiple ticker symbols.
- Classifies headlines as `bullish`, `bearish`, or `neutral` using Groq.
- Generates a concise explanation for every sentiment classification.
- Displays aggregate sentiment statistics and interactive result filters.
- Validates ticker symbols and incoming analysis requests on the backend.
- Handles invalid credentials, rate limits, timeouts, and upstream failures with
  actionable error messages.
- Keeps Finnhub and Groq credentials exclusively on the server.
- Includes mocked backend integration tests and dependency-free frontend tests.

## How it works

```text
Browser
   │
   ├── GET /api/news/<ticker> ──────── Flask ──────── Finnhub
   │
   └── POST /api/analyse-news ─────── Flask ──────── Groq
                                      │
                                      └── Validated sentiment JSON
```

Flask serves the modular frontend and both API endpoints from the same origin.
The browser never receives either third-party API key. Groq is constrained with
a strict JSON schema, and the backend validates its output before returning
enriched articles to the dashboard.

## Technology

- Python, Flask, and Requests
- Vanilla JavaScript ES modules
- HTML and CSS
- Finnhub company-news API
- Groq Chat Completions API with `openai/gpt-oss-20b`
- pytest and the Node.js test runner

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
