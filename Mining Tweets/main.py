import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import tweepy


HOST = "127.0.0.1"
PORT = 8000


def load_twitter_client() -> tweepy.Client:
    """Create a Tweepy client from environment variables."""
    bearer_token = os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        raise RuntimeError(
            "Missing X_BEARER_TOKEN. Set it before starting the server."
        )

    # wait_on_rate_limit makes Tweepy pause instead of failing immediately
    # when the API returns a rate-limit response.
    return tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)


def serialize(obj):
    """Convert Tweepy objects and nested data into JSON-safe values."""
    if obj is None:
        return None

    if hasattr(obj, "_asdict"):
        return {key: serialize(value) for key, value in obj._asdict().items()}

    if isinstance(obj, dict):
        return {key: serialize(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]

    if hasattr(obj, "data"):
        return serialize(obj.data)

    return obj


def json_response(handler: BaseHTTPRequestHandler, status_code: int, payload: dict):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class TwitterAPIHandler(BaseHTTPRequestHandler):
    client = None

    def log_message(self, format, *args):
        # Keep the console output focused on API responses.
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        if path == "/":
            return json_response(
                self,
                200,
                {
                    "message": "Tweepy REST API is running",
                    "routes": {
                        "/health": "Health check",
                        "/tweets/search?query=...": "Search recent tweets",
                        "/users/<username>": "Look up a user by username",
                    },
                },
            )

        if path == "/health":
            return json_response(self, 200, {"status": "ok"})

        if path == "/tweets/search":
            return self.handle_search_tweets(query_params)

        if path.startswith("/users/"):
            username = path.removeprefix("/users/").strip("/")
            if not username:
                return json_response(
                    self,
                    400,
                    {"error": "Username is required in the URL path."},
                )
            return self.handle_get_user(username)

        return json_response(self, 404, {"error": "Route not found"})

    def handle_search_tweets(self, query_params):
        query = query_params.get("query", [""])[0].strip()
        max_results_raw = query_params.get("max_results", ["10"])[0]

        if not query:
            return json_response(
                self,
                400,
                {"error": "Missing required query parameter: query"},
            )

        try:
            max_results = int(max_results_raw)
        except ValueError:
            return json_response(
                self,
                400,
                {"error": "max_results must be an integer"},
            )

        if not 10 <= max_results <= 100:
            return json_response(
                self,
                400,
                {"error": "max_results must be between 10 and 100"},
            )

        try:
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=["created_at", "lang", "author_id", "public_metrics"],
            )
        except tweepy.TweepyException as exc:
            return json_response(self, 502, {"error": str(exc)})

        tweets = serialize(response.data) if response.data else []

        return json_response(
            self,
            200,
            {
                "query": query,
                "count": len(tweets),
                "tweets": tweets,
                "meta": serialize(response.meta),
            },
        )

    def handle_get_user(self, username):
        try:
            response = self.client.get_user(
                username=username,
                user_fields=["created_at", "description", "public_metrics", "verified"],
            )
        except tweepy.TweepyException as exc:
            return json_response(self, 502, {"error": str(exc)})

        return json_response(
            self,
            200,
            {
                "user": serialize(response.data),
                "meta": serialize(response.meta),
            },
        )


def main():
    TwitterAPIHandler.client = load_twitter_client()

    server = ThreadingHTTPServer((HOST, PORT), TwitterAPIHandler)
    print(f"Serving on http://{HOST}:{PORT}")
    print("Try:")
    print("  /health")
    print("  /tweets/search?query=python&max_results=10")
    print("  /users/jack")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
