import requests
import config


city = input("Enter city: ")
coords = get_coordinates(city)
weather = get_weather(city)

show_weather(city, weather)