from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid credentials, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save for next runs
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service



if __name__ == "__main__":
    service = get_service()
    events_result = service.events().list(calendarId="primary", maxResults=5).execute()
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
    else:
        print("Upcoming events:")
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            print(f"- {start}: {e['summary']}")

