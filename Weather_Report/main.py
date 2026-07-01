from geocoding import get_location
from weather_api import get_weather
from display import show_weather

city = input("Enter city: ")
location = get_location(city)
if location is not None:
    weather = get_weather(location)
    result = show_weather(city, weather)
else:
    print("City not found.")
