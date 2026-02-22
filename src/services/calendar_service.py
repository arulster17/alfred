import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes for dual authentication approach
# User scope: Read-only access to all calendars (for viewing schedule)
# Note: calendar.readonly includes both calendar list access AND event reading
USER_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Bot scope: Full access (but only has ACL permissions to bot calendar)
BOT_SCOPES = ['https://www.googleapis.com/auth/calendar']

# Get project root directory relative to this file
# Path: src/services/calendar_service.py -> go up to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# User credentials (for reading all calendars)
USER_CREDENTIALS_PATH = PROJECT_ROOT / 'credentials' / 'user_credentials.json'
USER_TOKEN_PATH = PROJECT_ROOT / 'user_token.pickle'

# Bot credentials (for writing to bot calendar only)
BOT_CREDENTIALS_PATH = PROJECT_ROOT / 'credentials' / 'bot_credentials.json'
BOT_TOKEN_PATH = PROJECT_ROOT / 'bot_token.pickle'

def _get_service(credentials_path, token_path, scopes, service_type="calendar"):
    """
    Generic authentication function for both user and bot credentials.

    Args:
        credentials_path: Path to credentials JSON file
        token_path: Path to store token pickle
        scopes: List of OAuth scopes
        service_type: Type of service ("user" or "bot") for error messages

    Returns:
        Google Calendar service instance
    """
    creds = None

    # Token file stores access and refresh tokens
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Need credentials.json from Google Cloud Console
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"{service_type.title()} credentials not found at {credentials_path}\n"
                    f"Please download OAuth credentials from Google Cloud Console\n"
                    f"and save to: {credentials_path}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), scopes)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_read_service():
    """
    Get Calendar service with READ-ONLY access to all calendars.

    Used for:
    - Viewing schedule ("what's my schedule today")
    - Reading events from any calendar
    - No modification permissions

    Returns:
        Google Calendar service instance (readonly)
    """
    return _get_service(USER_CREDENTIALS_PATH, USER_TOKEN_PATH, USER_SCOPES, "user")

def get_write_service():
    """
    Get Calendar service with WRITE access to bot calendar only.

    Used for:
    - Creating new events
    - Modifying events
    - Only has ACL permissions to bot calendar (physical isolation)

    Returns:
        Google Calendar service instance (bot calendar only)
    """
    return _get_service(BOT_CREDENTIALS_PATH, BOT_TOKEN_PATH, BOT_SCOPES, "bot")

# Legacy function for backwards compatibility
def get_calendar_service():
    """
    Legacy function - returns write service.
    Use get_read_service() or get_write_service() directly instead.
    """
    return get_write_service()

def create_calendar_event(event_data):
    """
    Create a calendar event in bot calendar.

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
    service = get_write_service()

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
    Search for calendar events in bot calendar by text query.

    Args:
        query (str): Search query (searches title, description, location)
        max_results (int): Maximum number of events to return
        time_min (datetime): Only return events after this time (default: now)
        time_max (datetime): Only return events before this time (optional)

    Returns:
        list: List of matching events
    """
    service = get_write_service()  # Search in bot calendar for modifications
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

    # Default to searching from now onwards
    if time_min is None:
        time_min = datetime.now(timezone.utc)

    def _to_rfc3339(dt):
        """Convert datetime to RFC3339 string with Z suffix, works on all platforms."""
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')  # assume UTC if naive

    params = {
        'calendarId': calendar_id,
        'q': query,  # Free text search
        'maxResults': max_results,
        'singleEvents': True,
        'orderBy': 'startTime',
        'timeMin': _to_rfc3339(time_min),
    }

    if time_max:
        params['timeMax'] = _to_rfc3339(time_max)

    events_result = service.events().list(**params).execute()
    events = events_result.get('items', [])

    print(f"🔍 Found {len(events)} event(s) matching '{query}'")
    return events


def modify_event(event_id, updates):
    """
    Modify an existing calendar event in bot calendar.

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
    service = get_write_service()
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

    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return events
