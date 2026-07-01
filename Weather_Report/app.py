from flask import Flask, render_template, request
import requests

from geocoding import get_location
from weather_api import get_weather


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    city = "Berlin"
    weather = None
    error = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()

    if city:
        try:
            location = get_location(city)
            if location is None:
                error = f"We could not find weather data for {city}."
            else:
                weather = get_weather(location)
        except requests.RequestException:
            error = "The weather service did not respond. Please try again."
        except (KeyError, IndexError, ValueError):
            error = "The weather data came back in an unexpected format."

    return render_template("index.html", city=city, weather=weather, error=error)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
