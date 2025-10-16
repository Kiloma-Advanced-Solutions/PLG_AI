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
def create_file(content: str, file_name) -> str:
    """
    Create a new text file with the given file name and content and return its absolute path.
    Use this tool whenever the user asks to create a file.
    IMPORTANT: Always return the tool’s output directly to the user.   
    """
    import os

    try:
        file_path = f"{file_name}.txt" if not file_name.lower().endswith(".txt") else file_name

        with open(file_path, "w") as f:
            f.write(content)
        abs_path = os.path.abspath(file_path)
        return f"✅ הקובץ נוצר לבקשתך. ניתן לצפות בו בנתיב: {abs_path}"
        
    except Exception as e:
        return f"❌ שגיאה ביצירת קובץ: {e}"


@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Read a text file and return its content.
    Use this tool whenever the user asks to see or read the contents of a file.
    The 'file_path' parameter should be the full path to the file.
    IMPORTANT: Always return the tool’s output directly to the user.   
    """
    import os

    # Normalize the path - handle both absolute and relative paths
    if not file_path.startswith('/'):
        file_path = '/' + file_path
    
    # Also try just the filename if the full path doesn't exist
    if not os.path.exists(file_path):
        # Try just the filename in current directory
        filename_only = os.path.basename(file_path)
        if os.path.exists(filename_only):
            file_path = filename_only
        else:
            return f"❌ הקובץ לא נמצא: {file_path}"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"📄 תוכן הקובץ:`{os.path.abspath(file_path)}`:\n\n{content}"
    except Exception as e:
        return f"❌ שגיאה בקריאת קובץ: {e}"


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

