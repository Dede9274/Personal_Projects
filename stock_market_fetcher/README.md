# PulseStock

PulseStock serves a small modular frontend and a Flask API from the same local
server. Finnhub and Anthropic credentials are read only by Flask; they are never
included in browser code or browser requests.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FINNHUB_API_KEY="your-finnhub-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
python3 finnhub_proxy.py
```

Open <http://localhost:5050>.

`ANTHROPIC_MODEL` can optionally override the default model.

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
```
