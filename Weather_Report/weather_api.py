import requests 
from config import BASE_URL

WEATHER_CODE_DETAILS = {
    0: ("Clear sky", "sunny"),
    1: ("Mostly clear", "sunny"),
    2: ("Partly cloudy", "cloudy"),
    3: ("Overcast", "cloudy"),
    45: ("Fog", "foggy"),
    48: ("Rime fog", "foggy"),
    51: ("Light drizzle", "rainy"),
    53: ("Drizzle", "rainy"),
    55: ("Heavy drizzle", "rainy"),
    61: ("Light rain", "rainy"),
    63: ("Rain", "rainy"),
    65: ("Heavy rain", "rainy"),
    71: ("Light snow", "snowy"),
    73: ("Snow", "snowy"),
    75: ("Heavy snow", "snowy"),
    80: ("Light showers", "rainy"),
    81: ("Showers", "rainy"),
    82: ("Heavy showers", "rainy"),
    95: ("Thunderstorm", "stormy"),
    96: ("Thunderstorm with hail", "stormy"),
    99: ("Heavy thunderstorm with hail", "stormy"),
}


def _round_average(values):
    usable_values = [value for value in values if value is not None]
    if not usable_values:
        return None
    return round(sum(usable_values) / len(usable_values), 1)


def _describe_weather(code):
    description, theme = WEATHER_CODE_DETAILS.get(code, ("Forecast", "cloudy"))
    return {
        "code": code,
        "description": description,
        "theme": theme
    }


def _temperature_theme(level):
    if level < 0.18:
        return "cold"
    if level < 0.38:
        return "cool"
    if level < 0.65:
        return "mild"
    if level < 0.88:
        return "warm"
    return "hot"


def get_weather(location):
    latitude = location["latitude"]
    longitude = location["longitude"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
        "forecast_days": 7,
        "timezone": "auto"
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    hourly = data["hourly"]
    daily = data["daily"]
    first_day_temperatures = hourly["temperature_2m"][:24]
    lowest_hour_temperature = min(first_day_temperatures)
    hourly_temperature_range = max(first_day_temperatures) - lowest_hour_temperature or 1
    hours = []
    for index, time in enumerate(hourly["time"][:24]):
        temperature = hourly["temperature_2m"][index]
        temperature_level = round((temperature - lowest_hour_temperature) / hourly_temperature_range, 2)
        hours.append({
            "time": time,
            "label": time.split("T")[1],
            "temperature": temperature,
            "temperature_level": temperature_level,
            "temperature_theme": _temperature_theme(temperature_level),
            "humidity": hourly["relative_humidity_2m"][index],
            "wind_speed": hourly["wind_speed_10m"][index]
        })

    days = []
    for index, date in enumerate(daily["time"]):
        condition = _describe_weather(daily["weather_code"][index])
        days.append({
            "date": date,
            "label": date[5:],
            "high": daily["temperature_2m_max"][index],
            "low": daily["temperature_2m_min"][index],
            "precipitation": daily["precipitation_probability_max"][index],
            "wind_speed": daily["wind_speed_10m_max"][index],
            "condition": condition["description"],
            "theme": condition["theme"]
        })

    temperatures = [hour["temperature"] for hour in hours]
    humidity = [hour["humidity"] for hour in hours]
    wind_speeds = [hour["wind_speed"] for hour in hours]
    current_condition = _describe_weather(data.get("current", {}).get("weather_code"))

    return {
        "location": location,
        "current": data.get("current", {}),
        "condition": current_condition,
        "units": {
            "current": data.get("current_units", {}),
            "hourly": data.get("hourly_units", {}),
            "daily": data.get("daily_units", {})
        },
        "summary": {
            "high": max(temperatures),
            "low": min(temperatures),
            "average_temperature": _round_average(temperatures),
            "average_humidity": _round_average(humidity),
            "peak_wind": max(wind_speeds),
            "elevation": data.get("elevation"),
            "timezone": data.get("timezone")
        },
        "hours": hours,
        "days": days
    }
