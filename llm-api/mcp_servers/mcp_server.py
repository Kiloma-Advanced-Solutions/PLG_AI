from mcp.server.fastmcp import FastMCP
import logging
import traceback

mcp = FastMCP("Demo", port=8000)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


@mcp.tool()
def time() -> str:
    """Get the current time in Israel (Asia/Jerusalem)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    israel_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    return israel_time.strftime('%H:%M:%S')  # convert to string

    
@mcp.tool()
def get_cat_message(message: str) -> str:
    """Get a cat image with a personal message, formatted as Markdown."""
    import requests
    from urllib.parse import quote

    message_encoded = quote(message)
    url = f"https://cataas.com/cat/says/{message_encoded}"

    response = requests.get(url)
    if response.status_code == 200:
        # Return a Markdown image tag so the chatbot renders it directly (<![alt text](image_url)>)
        return f"![החתול אומר {message}](https://cataas.com/cat/says/{message_encoded})"
    else:
        return f"❌ נכשל באחזור התמונה (status {response.status_code})."




if __name__ == "__main__":
    mcp.run(transport="streamable-http")

