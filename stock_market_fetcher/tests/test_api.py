import pytest
import requests

from stock_market_fetcher import finnhub_proxy as api


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


@pytest.fixture(autouse=True)
def configured_api(monkeypatch):
    monkeypatch.setattr(api, "FINNHUB_API_KEY", "server-finnhub-key")
    monkeypatch.setattr(api, "ANTHROPIC_API_KEY", "server-anthropic-key")


@pytest.fixture
def client():
    api.app.config.update(TESTING=True)
    return api.app.test_client()


@pytest.fixture
def article():
    return {
        "ticker": "NVDA",
        "headline": "Chip demand rises",
        "summary": "Demand increased.",
        "source": "Example",
        "url": "https://example.com/news",
        "datetime": 1_700_000_000,
    }


def anthropic_payload(sentiment="bullish", reason="Demand is rising"):
    return {
        "content": [{
            "text": (
                f'[{{"index": 1, "sentiment": "{sentiment}", '
                f'"reason": "{reason}"}}]'
            )
        }]
    }


def test_index_serves_modular_frontend(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'<script type="module" src="/js/app.js"></script>' in response.data


def test_health_reports_both_services(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "services": {"finnhub": True, "anthropic": True},
    }


def test_invalid_ticker_returns_400(client):
    response = client.get("/api/news/not_a_ticker")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid ticker symbol"


def test_missing_finnhub_key_returns_503(client, monkeypatch):
    monkeypatch.setattr(api, "FINNHUB_API_KEY", "")

    response = client.get("/api/news/NVDA")

    assert response.status_code == 503


def test_news_uses_server_key_and_ignores_query_token(client, monkeypatch, article):
    get_calls = []

    def fake_get(url, **kwargs):
        get_calls.append((url, kwargs))
        return FakeResponse([article])

    monkeypatch.setattr(api.requests, "get", fake_get)

    response = client.get("/api/news/nvda?token=browser-key")

    assert response.status_code == 200
    assert response.get_json()[0]["ticker"] == "NVDA"
    assert get_calls[0][1]["params"]["token"] == "server-finnhub-key"
    assert "browser-key" not in repr(get_calls)


def test_finnhub_failure_returns_sanitized_502(client, monkeypatch):
    def fail(*args, **kwargs):
        raise requests.ConnectionError("request failed with secret details")

    monkeypatch.setattr(api.requests, "get", fail)

    response = client.get("/api/news/NVDA")

    assert response.status_code == 502
    assert response.get_json() == {"error": "Unable to fetch news from Finnhub"}
    assert "secret details" not in response.get_data(as_text=True)


@pytest.mark.parametrize("payload", [None, {}, {"articles": "not-a-list"}, {"articles": []}])
def test_invalid_articles_payload_returns_400(client, payload):
    response = client.post("/api/analyse-news", json=payload)

    assert response.status_code == 400


def test_more_than_60_articles_returns_400(client, article):
    response = client.post("/api/analyse-news", json={"articles": [article] * 61})

    assert response.status_code == 400


def test_invalid_article_returns_400(client, article):
    invalid_article = {**article, "headline": ""}

    response = client.post("/api/analyse-news", json={"articles": [invalid_article]})

    assert response.status_code == 400


def test_missing_anthropic_key_returns_503(client, monkeypatch, article):
    monkeypatch.setattr(api, "ANTHROPIC_API_KEY", "")

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.status_code == 503


def test_malformed_anthropic_json_returns_502(client, monkeypatch, article):
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"content": [{"text": "not JSON"}]}),
    )

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.status_code == 502
    assert response.get_json() == {"error": "Unable to analyse news sentiment"}


def test_unsupported_sentiment_is_ignored(client, monkeypatch, article):
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(anthropic_payload("excited")),
    )

    response = client.post("/api/analyse-news", json={"articles": [article]})

    result = response.get_json()["articles"][0]
    assert response.status_code == 200
    assert result["sentiment"] == "neutral"
    assert result["reason"] == ""


def test_analysis_returns_enriched_article_and_uses_server_key(
    client, monkeypatch, article
):
    post_calls = []

    def fake_post(url, **kwargs):
        post_calls.append((url, kwargs))
        return FakeResponse(anthropic_payload())

    monkeypatch.setattr(api.requests, "post", fake_post)

    response = client.post("/api/analyse-news", json={"articles": [article]})

    result = response.get_json()["articles"][0]
    assert response.status_code == 200
    assert result["ticker"] == "NVDA"
    assert result["sentiment"] == "bullish"
    assert result["reason"] == "Demand is rising"
    assert post_calls[0][1]["headers"]["x-api-key"] == "server-anthropic-key"
    assert "server-anthropic-key" not in repr(post_calls[0][1]["json"])


def test_out_of_range_score_index_defaults_to_neutral(client, monkeypatch, article):
    payload = {
        "content": [{
            "text": '[{"index": 2, "sentiment": "bearish", "reason": "Bad"}]'
        }]
    }
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.get_json()["articles"][0]["sentiment"] == "neutral"
