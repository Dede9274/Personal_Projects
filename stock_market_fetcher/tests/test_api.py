import pytest
import requests

from stock_market_fetcher import finnhub_proxy as api


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 400

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


@pytest.fixture(autouse=True)
def configured_api(monkeypatch):
    monkeypatch.setattr(api, "FINNHUB_API_KEY", "server-finnhub-key")
    monkeypatch.setattr(api, "GROQ_API_KEY", "server-groq-key")


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


def groq_payload(sentiment="bullish", reason="Demand is rising"):
    return {
        "choices": [{
            "message": {"content": (
                f'{{"articles":[{{"index":1,"sentiment":"{sentiment}",'
                f'"reason":"{reason}"}}]}}'
            )}
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
        "services": {"finnhub": True, "groq": True},
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
    assert response.get_json() == {
        "error": "Cannot connect to Finnhub. Please try again."
    }
    assert "secret details" not in response.get_data(as_text=True)


@pytest.mark.parametrize("status_code", [401, 403])
def test_rejected_finnhub_key_returns_actionable_error(
    client, monkeypatch, status_code
):
    monkeypatch.setattr(
        api.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {"error": "Invalid API key"}, status_code=status_code
        ),
    )

    response = client.get("/api/news/NVDA")

    assert response.status_code == 502
    assert response.get_json() == {
        "error": (
            "Finnhub rejected FINNHUB_API_KEY. Set a valid key and restart "
            "the Flask server."
        )
    }


def test_finnhub_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setattr(
        api.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({}, status_code=429),
    )

    response = client.get("/api/news/NVDA")

    assert response.status_code == 429
    assert response.get_json() == {
        "error": "Finnhub rate limit reached. Wait a minute and try again."
    }


def test_finnhub_timeout_returns_504(client, monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout("request URL containing secret")

    monkeypatch.setattr(api.requests, "get", timeout)

    response = client.get("/api/news/NVDA")

    assert response.status_code == 504
    assert response.get_json() == {
        "error": "Finnhub timed out. Please try again."
    }
    assert "secret" not in response.get_data(as_text=True)


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


def test_missing_groq_key_returns_503(client, monkeypatch, article):
    monkeypatch.setattr(api, "GROQ_API_KEY", "")

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.status_code == 503


def test_malformed_groq_json_returns_502(client, monkeypatch, article):
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({
            "choices": [{"message": {"content": "not JSON"}}]
        }),
    )

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.status_code == 502
    assert response.get_json() == {"error": "Groq returned an invalid response."}


@pytest.mark.parametrize(
    ("status_code", "expected_status", "message_fragment"),
    [
        (400, 502, "rejected the request"),
        (401, 502, "rejected GROQ_API_KEY"),
        (403, 502, "does not have permission"),
        (404, 502, "is unavailable"),
        (413, 413, "Too many or overly long articles"),
        (429, 429, "rate limit reached"),
        (503, 503, "temporarily unavailable"),
    ],
)
def test_groq_http_errors_are_actionable(
    client, monkeypatch, article, status_code, expected_status, message_fragment
):
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({}, status_code=status_code),
    )

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.status_code == expected_status
    assert message_fragment in response.get_json()["error"]


def test_groq_timeout_returns_504(client, monkeypatch, article):
    def timeout(*args, **kwargs):
        raise requests.Timeout("request URL containing secret")

    monkeypatch.setattr(api.requests, "post", timeout)

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.status_code == 504
    assert response.get_json() == {
        "error": "Groq timed out. Please try again."
    }
    assert "secret" not in response.get_data(as_text=True)


def test_unsupported_sentiment_is_ignored(client, monkeypatch, article):
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(groq_payload("excited")),
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
        return FakeResponse(groq_payload())

    monkeypatch.setattr(api.requests, "post", fake_post)

    response = client.post("/api/analyse-news", json={"articles": [article]})

    result = response.get_json()["articles"][0]
    assert response.status_code == 200
    assert result["ticker"] == "NVDA"
    assert result["sentiment"] == "bullish"
    assert result["reason"] == "Demand is rising"
    assert post_calls[0][1]["headers"]["authorization"] == "Bearer server-groq-key"
    assert "server-groq-key" not in repr(post_calls[0][1]["json"])
    assert post_calls[0][1]["json"]["model"] == "openai/gpt-oss-20b"
    assert post_calls[0][1]["json"]["response_format"]["json_schema"]["strict"]


def test_out_of_range_score_index_defaults_to_neutral(client, monkeypatch, article):
    payload = {
        "choices": [{"message": {
            "content": (
                '{"articles":[{"index":2,"sentiment":"bearish",'
                '"reason":"Bad"}]}'
            )
        }}]
    }
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    response = client.post("/api/analyse-news", json={"articles": [article]})

    assert response.get_json()["articles"][0]["sentiment"] == "neutral"
