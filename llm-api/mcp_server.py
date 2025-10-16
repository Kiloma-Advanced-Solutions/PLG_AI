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

