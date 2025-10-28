# import os
# from google.auth.transport.requests import Request
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build

# SCOPES = ["https://www.googleapis.com/auth/calendar"]


# def get_service():
#     creds = None
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)

#     # If no valid credentials, start OAuth flow
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=8080)

#         # Save for next runs
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())

#     service = build("calendar", "v3", credentials=creds)
#     return service



# if __name__ == "__main__":
#     service = get_service()