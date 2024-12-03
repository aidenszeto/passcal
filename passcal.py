import os
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
import pickle

# Google Calendar API Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google():
    """Authenticate with Google using a service account."""
    credentials_info = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not credentials_info:
        print("Error: GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable must be set.")
        return None
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(credentials_info),
        scopes=SCOPES
    )
    # Build the Calendar API service
    return build('calendar', 'v3', credentials=credentials)

def fetch_satellite_passes():
    """Fetch satellite passes from the API."""
    # Satellite ID is fixed to 25544
    satellite_id = 25544

    # Retrieve observer parameters and API key from environment variables
    observer_lat = os.getenv("OBSERVER_LAT")
    observer_lng = os.getenv("OBSERVER_LNG")
    observer_alt = os.getenv("OBSERVER_ALT")
    api_key = os.getenv("API_KEY")

    # Validate environment variables
    if not all([observer_lat, observer_lng, observer_alt, api_key]):
        print("Error: OBSERVER_LAT, OBSERVER_LNG, OBSERVER_ALT, and API_KEY environment variables must be set.")
        return None

    try:
        # Convert numeric parameters to their appropriate types
        observer_lat = float(observer_lat)
        observer_lng = float(observer_lng)
        observer_alt = float(observer_alt)
    except ValueError:
        print("Error: OBSERVER_LAT, OBSERVER_LNG, and OBSERVER_ALT must be numeric values.")
        return None

    # Fixed parameters
    days = 10
    min_elevation = 70  # Updated as requested

    # Construct the API URL
    base_url = "https://api.n2yo.com/rest/v1/satellite/"
    endpoint = f"radiopasses/{satellite_id}/{observer_lat}/{observer_lng}/{observer_alt}/{days}/{min_elevation}"
    url = base_url + endpoint

    # Add the API key as a query parameter
    params = {"apiKey": api_key}

    try:
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse and return the JSON response
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def add_satellite_passes_to_calendar(service, api_response):
    """Add satellite passes to Google Calendar."""
    calendar_id = os.getenv("CALENDAR_ID", "primary")  # Default to 'primary' if not set
    passes = api_response['passes']
    
    for sat_pass in passes:
        start_utc = datetime.datetime.utcfromtimestamp(sat_pass['startUTC'])
        end_utc = datetime.datetime.utcfromtimestamp(sat_pass['endUTC'])
        
        event = {
            'summary': 'Satellite Pass - SPACE STATION',
            'description': (
                f"Start Direction: {sat_pass['startAzCompass']} ({sat_pass['startAz']}°)\n"
                f"Maximum Elevation: {sat_pass['maxEl']}° at {sat_pass['maxAzCompass']} ({sat_pass['maxAz']}°)\n"
                f"End Direction: {sat_pass['endAzCompass']} ({sat_pass['endAz']}°)"
            ),
            'start': {
                'dateTime': start_utc.isoformat() + 'Z',  # 'Z' indicates UTC time
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_utc.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
        }

        # Insert the event into the calendar
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Event created: {event_result.get('htmlLink')}")

def main():
    # Fetch satellite passes from the API
    api_response = fetch_satellite_passes()
    if not api_response:
        return

    # Authenticate and get the Calendar API service
    service = authenticate_google()
    if not service:
        return

    # Add satellite passes to the calendar
    add_satellite_passes_to_calendar(service, api_response)

if __name__ == '__main__':
    main()
