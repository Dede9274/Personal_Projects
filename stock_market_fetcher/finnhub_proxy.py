"""
Finnhub CORS Proxy — run this once on your machine:
    pip install flask flask-cors requests
    python finnhub_proxy.py

Then open the dashboard HTML file in your browser.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # allows browser to call this local server

FINNHUB_BASE = "https://finnhub.io/api/v1"

@app.route("/news/<ticker>")
def get_news(ticker):
    api_key = request.args.get("token", "")
    if not api_key:
        return jsonify({"error": "Missing token"}), 400

    to_date   = datetime.today().strftime("%Y-%m-%d")
    from_date = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")

    url = f"{FINNHUB_BASE}/company-news"
    params = {
        "symbol": ticker.upper(),
        "from":   from_date,
        "to":     to_date,
        "token":  api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json()

        # Return top 6, shaped for the dashboard
        result = []
        for a in articles[:6]:
            result.append({
                "ticker":   ticker.upper(),
                "headline": a.get("headline", ""),
                "summary":  a.get("summary") or a.get("headline", ""),
                "source":   a.get("source", "Finnhub"),
                "url":      a.get("url", ""),
                "datetime": a.get("datetime", 0),
            })
        return jsonify(result)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("\n  Finnhub proxy running at http://localhost:5050")
    print("  Keep this terminal open while using the dashboard.\n")
    app.run(port=5050, debug=False)
