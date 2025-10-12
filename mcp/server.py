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
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime('%H:%M:%S')

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
