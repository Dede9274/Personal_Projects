import requests
from config import GEOCODE_URL

def get_location(city):
    params = {
        "q": city,
        "api_key": "6a42e47417094352493777kdg94657a"
    }

    response = requests.get(GEOCODE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data:
        return None
    
    first_result = data[0]
    latitude = float(first_result["lat"])
    longitude = float(first_result["lon"])

    return {
        "city": first_result.get("display_name", city),
        "latitude": latitude,
        "longitude": longitude
    }
