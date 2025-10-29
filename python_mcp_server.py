"""
Python MCP Server using FastMCP
Provides additional tools for the chatbot including Google Flights integration
"""
from fastmcp import FastMCP
from datetime import datetime
import os
import requests
import json
import asyncio
from typing import Optional
from pydantic import BaseModel
import dotenv
# This server focuses on utility tools: calculate_area, get_file_info, get_system_info
dotenv.load_dotenv()


mcp = FastMCP("Python Tools Server")

class FlightQuery(BaseModel):
    origin: str
    destination: str
    date: str



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

@mcp.tool()
def search_flights(origin: str, destination: str, date: str, return_date: str = None) -> str:
    """
    Search for flights between two airports using SerpAPI Google Flights.
    
    Args:
        origin: Origin airport code (e.g., "TLV", "JFK", "LAX")
        destination: Destination airport code (e.g., "BER", "LHR", "CDG")
        date: The departure date (YYYY-MM-DD format)
        return_date: Return date for round-trip flights (YYYY-MM-DD format, optional)
    
    Returns:
        Flight search results in Hebrew
    """

    from serpapi import GoogleSearch
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    params = {
    "api_key": serpapi_key,
    "engine": "google_flights",
    "hl": "en",
    "gl": "us",
    "departure_id": origin,
    "arrival_id": destination,
    "outbound_date": date,
    "return_date": return_date,
    "currency": "USD"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    
    # Check for errors
    if "error" in results:
        return f"❌ שגיאה ב-SerpAPI: {results['error']}"
    
    # Check if we have flight results
    if "best_flights" not in results or not results["best_flights"]:
        return f"❌ לא נמצאו טיסות מ{origin} ל{destination} בתאריך {date}"
    
    flights = results["best_flights"]
    
    # Format results in Hebrew - concise version
    trip_type = "הלוך ושוב" if return_date else "כיוון אחד"
    result = f"✈️ טיסות {trip_type} מ{origin} ל{destination}:\n"
    result += f"📅 תאריך יציאה: {date}"
    if return_date:
        result += f" | תאריך חזרה: {return_date}"
    result += f"\n\n"
    
    # Show top 3 flights only
    for i, flight in enumerate(flights[:3], 1):
        flight_segments = flight.get("flights", [])
        if not flight_segments:
            continue
            
        first_segment = flight_segments[0]
        last_segment = flight_segments[-1]
        
        # Extract basic info
        airline = first_segment.get("airline", "Unknown")
        departure_airport = first_segment.get("departure_airport", {})
        arrival_airport = last_segment.get("arrival_airport", {})
        
        departure_time = departure_airport.get("time", "N/A")
        arrival_time = arrival_airport.get("time", "N/A")
        
        # Format times to show only time part
        if departure_time != "N/A" and "T" in departure_time:
            departure_time = departure_time.split("T")[1][:5]
        if arrival_time != "N/A" and "T" in arrival_time:
            arrival_time = arrival_time.split("T")[1][:5]
        
        total_duration = flight.get("total_duration", "N/A")
        price = flight.get("price", "N/A")
        
        # Count stops
        stops = len(flight_segments) - 1
        stops_text = "ללא עצירות" if stops == 0 else f"{stops} עצירה"
        
        # Format price
        price_text = f"${price}" if price != "N/A" else "מחיר לא זמין"
        
        result += f"{i}. {airline}\n"
        result += f"   🕐 {departure_time} → {arrival_time} ({total_duration} דקות)\n"
        result += f"   🛫 {stops_text} | 💰 {price_text}\n\n"
    
    result += f"📊 נמצאו {len(flights)} טיסות זמינות"
    return result


if __name__ == "__main__":
    # Run the MCP server with streamable HTTP transport
    PORT = 8002
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
    print("Python MCP server listening on http://localhost:${PORT}");
    print("Python MCP endpoint: http://localhost:${PORT}/mcp");


