

def show_weather(city, weather):
    print("                 ")
    print("                 ")
    print("---------------------")
    print(f"Weather for {city}")
    print("---------------------")
    print(f"Current time: {weather['current'].get('time')}")
    print(f"Current temperature: {weather['current'].get('temperature_2m')}")
    print(f"Condition: {weather['condition']['description']}")
    print(f"High: {weather['summary']['high']}")
    print(f"Low: {weather['summary']['low']}")
     
