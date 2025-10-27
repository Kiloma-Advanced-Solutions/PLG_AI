from mcp.server.fastmcp import FastMCP
from google_calendar_mcp import get_service
from datetime import datetime

mcp = FastMCP("Demo")

@mcp.tool()
def time() -> str:
    """Get the current time in Israel (Asia/Jerusalem)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    israel_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    return israel_time.strftime('%d/%m/%Y, %H:%M:%S')  # convert to string


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
def get_calendar_events(max_results: int = 10) -> str:
    """
    Get upcoming Google Calendar events.
    Args:
        max_results: Maximum number of events to return (default: 10)
    Returns: A formatted string with upcoming meetings
    """
    try:
        service = get_service()
        now = datetime.utcnow().isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "📅 אין אירועים קרבים במערכת שלך."
        
        result = f"📅 יש לך {len(events)} אירועים קרבים:\n\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Format the date
            try:
                if 'T' in start:
                    # DateTime format
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    formatted_start = dt.strftime('%d/%m/%Y %H:%M')
                else:
                    # Date only format
                    dt = datetime.fromisoformat(start)
                    formatted_start = dt.strftime('%d/%m/%Y')
            except:
                formatted_start = start
            
            summary = event.get('summary', 'ללא כותרת')
            result += f"🗓️ {formatted_start}: {summary}\n"
        
        return result
        
    except Exception as e:
        return f"❌ שגיאה בטעינת יומן: {str(e)}"


@mcp.tool()
def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = ""
) -> str:
    """
    Create a new Google Calendar event.
    Args:
        summary: Event title
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or just date (YYYY-MM-DD)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS) or just date (YYYY-MM-DD)
        description: Optional event description
    Returns: Confirmation message
    """
    try:
        service = get_service()
        
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Jerusalem',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Jerusalem',
            },
        }
        
        if description:
            event['description'] = description
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        return f"✅ האירוע '{summary}' נוצר בהצלחה! זמן: {start_time}"
        
    except Exception as e:
        return f"❌ שגיאה ביצירת אירוע: {str(e)}"


@mcp.tool()
def search_calendar_events(query: str, max_results: int = 5) -> str:
    """
    Search for Google Calendar events by keyword.
    Args:
        query: Search term (e.g., "meeting", "project")
        max_results: Maximum number of results to return (default: 5)
    Returns: Matching calendar events
    """
    try:
        service = get_service()
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Get upcoming events and filter by query
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=100,  # Get more to search through
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Filter events by search query
        matching_events = []
        for event in events:
            summary = event.get('summary', '').lower()
            description = event.get('description', '').lower()
            if query.lower() in summary or query.lower() in description:
                matching_events.append(event)
        
        if not matching_events:
            return f"📭 לא נמצאו אירועים עם המילה '{query}'"
        
        # Limit results
        matching_events = matching_events[:max_results]
        
        result = f"🔍 נמצאו {len(matching_events)} אירועים עבור '{query}':\n\n"
        for event in matching_events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            try:
                if 'T' in start:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    formatted_start = dt.strftime('%d/%m/%Y %H:%M')
                else:
                    dt = datetime.fromisoformat(start)
                    formatted_start = dt.strftime('%d/%m/%Y')
            except:
                formatted_start = start
            
            summary = event.get('summary', 'ללא כותרת')
            result += f"🗓️ {formatted_start}: {summary}\n"
        
        return result
        
    except Exception as e:
        return f"❌ שגיאה בחיפוש יומן: {str(e)}"


@mcp.tool()
def get_past_calendar_events(max_results: int = 10) -> str:
    """
    Get past Google Calendar events.
    Args:
        max_results: Maximum number of events to return (default: 10)
    Returns: A formatted string with past meetings
    """
    try:
        service = get_service()
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Get past events (reverse order, most recent first)
        events_result = service.events().list(
            calendarId='primary',
            timeMax=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "📅 אין אירועים קודמים במערכת שלך."
        
        # Reverse to show most recent first
        events = list(reversed(events))
        
        result = f"📅 יש לך {len(events)} אירועים קודמים:\n\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Format the date
            try:
                if 'T' in start:
                    # DateTime format
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    formatted_start = dt.strftime('%d/%m/%Y %H:%M')
                else:
                    # Date only format
                    dt = datetime.fromisoformat(start)
                    formatted_start = dt.strftime('%d/%m/%Y')
            except:
                formatted_start = start
            
            summary = event.get('summary', 'ללא כותרת')
            result += f"🗓️ {formatted_start}: {summary}\n"
        
        return result
        
    except Exception as e:
        return f"❌ שגיאה בטעינת יומן: {str(e)}"


@mcp.tool()
def get_all_calendar_events(max_results: int = 20, past_days: int = 90) -> str:
    """
    Get all Google Calendar events from the past X days and future.
    Args:
        max_results: Maximum number of events to return (default: 20)
        past_days: Number of days in the past to look back (default: 90)
    Returns: A formatted string with all meetings
    """
    try:
        service = get_service()
        from datetime import timedelta
        
        # Calculate time range
        now = datetime.utcnow()
        past_time = now - timedelta(days=past_days)
        time_min = past_time.isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"📅 אין אירועים ב-{past_days} הימים האחרונים ובעתיד."
        
        # Separate past and future
        current_time = datetime.utcnow()
        past_events = []
        future_events = []
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            try:
                if 'T' in start:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(start)
                
                if dt < current_time:
                    past_events.append((dt, event))
                else:
                    future_events.append((dt, event))
            except:
                pass
        
        result = f"📅 מעל {past_days} הימים האחרונים:\n"
        
        if past_events:
            result += f"\n📜 אירועים קודמים ({len(past_events)}):\n"
            for dt, event in past_events:
                formatted_start = dt.strftime('%d/%m/%Y %H:%M')
                summary = event.get('summary', 'ללא כותרת')
                result += f"  🗓️ {formatted_start}: {summary}\n"
        
        if future_events:
            result += f"\n📅 אירועים קרבים ({len(future_events)}):\n"
            for dt, event in future_events:
                formatted_start = dt.strftime('%d/%m/%Y %H:%M')
                summary = event.get('summary', 'ללא כותרת')
                result += f"  🗓️ {formatted_start}: {summary}\n"
        
        return result
        
    except Exception as e:
        return f"❌ שגיאה בטעינת יומן: {str(e)}"

    
if __name__ == "__main__":
    mcp.run(transport="streamable-http")