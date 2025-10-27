"""
Python MCP Server using FastMCP
Provides additional tools for the chatbot
"""
from fastmcp import FastMCP
from datetime import datetime
import os
import requests

mcp = FastMCP("Python Tools Server")

@mcp.tool()
def calculate_area(shape: str, width: float, height: float = None) -> str:
    """Calculate the area of a shape.
    
    Args:
        shape: The shape type (rectangle, square, triangle)
        width: The width of the shape
        height: The height of the shape (required for rectangle/triangle)
    
    Returns:
        The area calculation result
    """
    if shape.lower() == "square":
        area = width * width
        return f"✅ שטח הריבוע: {area} (רוחב: {width} × {width})"
    elif shape.lower() == "rectangle":
        if height is None:
            return "❌ שגיאה: נדרש גם גובה למלבן"
        area = width * height
        return f"✅ שטח המלבן: {area} (רוחב: {width} × גובה: {height})"
    elif shape.lower() == "triangle":
        if height is None:
            return "❌ שגיאה: נדרש גם גובה למשולש"
        area = 0.5 * width * height
        return f"✅ שטח המשולש: {area} (0.5 × {width} × {height})"
    else:
        return f"❌ צורה לא נתמכת: {shape}. אפשרויות: square, rectangle, triangle"

@mcp.tool()
def get_file_info(file_path: str) -> str:
    """Get information about a file (size, exists, etc).
    
    Args:
        file_path: The path to the file
    
    Returns:
        File information
    """
    try:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            is_dir = os.path.isdir(file_path)
            
            result = f"📄 מידע על הקובץ: {file_path}\n"
            result += f"קיים: ✅\n"
            result += f"גודל: {size} bytes\n"
            result += f"סוג: {'תיקייה' if is_dir else 'קובץ'}\n"
            
            if not is_dir:
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                result += f"שונה לאחרונה: {modified.strftime('%d/%m/%Y %H:%M')}"
            
            return result
        else:
            return f"❌ הקובץ לא נמצא: {file_path}"
    except Exception as e:
        return f"❌ שגיאה: {e}"



@mcp.tool()
def get_system_info() -> str:
    """Get information about the current system.
    
    Returns:
        System information
    """
    import platform
    
    info = "🖥️ מידע על המערכת:\n"
    info += f"מערכת הפעלה: {platform.system()}\n"
    info += f"גרסה: {platform.version()}\n"
    info += f"מעבד: {platform.processor()}\n"
    info += f"מבנה: {platform.machine()}\n"
    
    try:
        import psutil
        info += f"זיכרון RAM: {psutil.virtual_memory().total / (1024**3):.2f} GB\n"
        info += f"מעבדים: {psutil.cpu_count()} cores\n"
    except ImportError:
        info += "(נדרש psutil לפרטים נוספים)\n"
    
    return info

if __name__ == "__main__":
    # Run the MCP server with streamable HTTP transport
    PORT = 8002
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
    print("Python MCP server listening on http://localhost:${PORT}");
    print("Python MCP endpoint: http://localhost:${PORT}/mcp");

