import logging
import traceback

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo1", port=8001)

logger = logging.getLogger(__name__)

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    logger.info("[MCP] add called", extra={"a": a, "b": b})
    print(f"[MCP] add called with a={a!r} (type={type(a)}), b={b!r} (type={type(b)})")
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    logger.info("[MCP] multiply called", extra={"a": a, "b": b})
    print(f"[MCP] multiply called with a={a!r} (type={type(a)}), b={b!r} (type={type(b)})")
    return a * b

@mcp.tool()
def get_pi() -> float:
    """Get the value of Pi."""
    logger.info("[MCP] get_pi called")
    print("[MCP] get_pi called")
    import math
    return math.pi
    

@mcp.tool()
def time() -> str:
    """Get the current time in Israel (Asia/Jerusalem)."""
    logger.info("[MCP] time called")
    print("[MCP] time called")
    from datetime import datetime
    from zoneinfo import ZoneInfo
    israel_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    return israel_time.strftime('%H:%M:%S')  # convert to string


@mcp.tool()
def create_file(content: str, file_name) -> str:
    """
    Create a new text file with the given file name and content and return its absolute path.
    Use this tool whenever the user asks to create a file.
    IMPORTANT: Always return the tool’s output directly to the user.   
    """
    logger.info(
        "[MCP] create_file called",
        extra={
            "file_name": file_name,
            "content_preview": content[:100] if isinstance(content, str) else str(type(content)),
        },
    )
    print(
        f"[MCP] create_file called with file_name={file_name!r} (type={type(file_name)}), "
        f"content_type={type(content)}"
    )
    import os

    try:
        file_path = f"{file_name}.txt" if not file_name.lower().endswith(".txt") else file_name

        with open(file_path, "w") as f:
            f.write(content)
        abs_path = os.path.abspath(file_path)
        return f"✅ הקובץ נוצר לבקשתך. ניתן לצפות בו בנתיב: {abs_path}"
        
    except Exception as e:
        traceback.print_exc()
        return f"❌ שגיאה ביצירת קובץ: {e}"


@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Read a text file and return its content.
    Use this tool whenever the user asks to see or read the contents of a file.
    The 'file_path' parameter should be the full path to the file.
    IMPORTANT: Always return the tool’s output directly to the user.   
    """
    logger.info("[MCP] read_file called", extra={"file_path": file_path})
    print(f"[MCP] read_file called with file_path={file_path!r} (type={type(file_path)})")
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
        traceback.print_exc()
        return f"❌ שגיאה בקריאת קובץ: {e}"



    
if __name__ == "__main__":
    mcp.run(transport="streamable-http")

