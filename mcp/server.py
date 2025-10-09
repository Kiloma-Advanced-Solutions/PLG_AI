from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo", port=8000)

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b

@mcp.tool()
def time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime('%H:%M:%S')

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
