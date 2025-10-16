from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo", port=8000)

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

@mcp.tool()
def time() -> str:
    """Get the current time in Israel (Asia/Jerusalem)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    israel_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    return israel_time.strftime('%H:%M:%S')  # convert to string

@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather of a city."""
    import requests
    from urllib.parse import quote

    city_encoded = quote(city)  # encode spaces and special characters
    url = f"https://wttr.in/{city_encoded}?format=j1"
    weather = requests.get(url).json()

    # current_condition is a list with one dict
    current = weather["current_condition"][0]
    
    # extract relevant fields
    weather_data = {
        "temp_C": current.get("temp_C"),
        "FeelsLikeC": current.get("FeelsLikeC"),
        "humidity": current.get("humidity"),
        "uvIndex": current.get("uvIndex"),
        "weatherDesc": current.get("weatherDesc")[0]["value"] if current.get("weatherDesc") else None,
        "windspeedKmph": current.get("windspeedKmph")
    }

    return str(weather_data)


@mcp.tool()
def get_pi() -> float:
    """Get the value of Pi."""
    import math
    return math.pi

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting."""
    return f"Hello, {name}!"

@mcp.resource("local://user")
def user_info():
    """Provide basic information about the current user."""
    import json
    return json.dumps({"name": "פלג אליהו", "age": 28})


    
if __name__ == "__main__":
    mcp.run(transport="streamable-http")

