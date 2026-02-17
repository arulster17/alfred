import os
import pickle
from datetime import datetime
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Get project root directory relative to this file
# Path: src/services/calendar_service.py -> go up to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# All paths relative to project root
CREDENTIALS_PATH = PROJECT_ROOT / 'credentials' / 'google_credentials.json'
TOKEN_PATH = PROJECT_ROOT / 'token.pickle'

def get_calendar_service():
    """
    Authenticate and return Google Calendar service instance.

    This function handles OAuth2 authentication flow:
    - First time: Opens browser for user to authorize
    - Subsequent times: Uses saved credentials from token.pickle
    """
    creds = None

    # Token file stores user's access and refresh tokens
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Need credentials.json from Google Cloud Console
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Google credentials not found at {CREDENTIALS_PATH}\n"
                    f"Please download OAuth credentials from Google Cloud Console\n"
                    f"and save to: {CREDENTIALS_PATH}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def create_calendar_event(event_data):
    """
    Create a calendar event in Google Calendar.

    Args:
        event_data (dict): Event details with structure:
            {
                'summary': str (required),
                'description': str (optional),
                'start': datetime (required),
                'end': datetime (required),
                'location': str (optional),
                'recurrence': str (optional) - RRULE format,
                'reminders': dict (optional) - reminder configuration
            }

    Returns:
        dict: Created event from Google Calendar API
    """
    service = get_calendar_service()

    # Build event object for Google Calendar API
    event = {
        'summary': event_data['summary'],
        'start': {
            'dateTime': event_data['start'].isoformat(),
            'timeZone': 'America/Los_Angeles',  # Change to your timezone
        },
        'end': {
            'dateTime': event_data['end'].isoformat(),
            'timeZone': 'America/Los_Angeles',  # Change to your timezone
        },
    }

    # Add optional fields
    if 'description' in event_data:
        event['description'] = event_data['description']

    if 'location' in event_data:
        event['location'] = event_data['location']

    # Add recurrence rule if specified
    if 'recurrence' in event_data:
        # Google Calendar expects recurrence as a list of RRULE strings
        recurrence_rule = event_data['recurrence']
        event['recurrence'] = [recurrence_rule]
        print(f"📅 Adding recurrence: {recurrence_rule}")

    # Add reminders if specified
    if 'reminders' in event_data:
        event['reminders'] = event_data['reminders']
        print(f"🔔 Adding reminders: {event_data['reminders']}")
    else:
        # Use default reminders if none specified
        event['reminders'] = {'useDefault': True}

    # Create the event
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    created_event = service.events().insert(
        calendarId=calendar_id,
        body=event
    ).execute()

    print(f"Event created: {created_event.get('htmlLink')}")
    return created_event

def search_events(query, max_results=100, time_min=None, time_max=None):
    """
    Search for calendar events by text query.

    Args:
        query (str): Search query (searches title, description, location)
        max_results (int): Maximum number of events to return
        time_min (datetime): Only return events after this time (default: now)
        time_max (datetime): Only return events before this time (optional)

    Returns:
        list: List of matching events
    """
    service = get_calendar_service()
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

    # Default to searching from now onwards
    if time_min is None:
        time_min = datetime.utcnow()

    params = {
        'calendarId': calendar_id,
        'q': query,  # Free text search
        'maxResults': max_results,
        'singleEvents': True,
        'orderBy': 'startTime',
        'timeMin': time_min.isoformat() + 'Z',
    }

    if time_max:
        params['timeMax'] = time_max.isoformat() + 'Z'

    events_result = service.events().list(**params).execute()
    events = events_result.get('items', [])

    print(f"🔍 Found {len(events)} event(s) matching '{query}'")
    return events


def modify_event(event_id, updates):
    """
    Modify an existing calendar event.

    Args:
        event_id (str): Google Calendar event ID
        updates (dict): Fields to update, can include:
            - 'summary': New title
            - 'description': New description
            - 'start': New start datetime
            - 'end': New end datetime
            - 'location': New location
            - 'recurrence': New recurrence rule
            - 'reminders': New reminder configuration

    Returns:
        dict: Updated event from Google Calendar API
    """
    service = get_calendar_service()
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

    # Get the existing event first
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

    # Apply updates
    if 'summary' in updates:
        event['summary'] = updates['summary']

    if 'description' in updates:
        event['description'] = updates['description']

    if 'location' in updates:
        event['location'] = updates['location']

    if 'start' in updates:
        event['start'] = {
            'dateTime': updates['start'].isoformat(),
            'timeZone': 'America/Los_Angeles',
        }

    if 'end' in updates:
        event['end'] = {
            'dateTime': updates['end'].isoformat(),
            'timeZone': 'America/Los_Angeles',
        }

    if 'recurrence' in updates:
        event['recurrence'] = [updates['recurrence']]

    if 'reminders' in updates:
        event['reminders'] = updates['reminders']

    # Update the event
    updated_event = service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=event
    ).execute()

    print(f"✏️ Event updated: {updated_event.get('htmlLink')}")
    return updated_event


def list_upcoming_events(max_results=10):
    """
    List upcoming events (optional utility function for testing).

    Args:
        max_results (int): Maximum number of events to return

    Returns:
        list: List of upcoming events
    """
    service = get_calendar_service()

    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return events
