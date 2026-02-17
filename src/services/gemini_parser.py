import os
import json
from google import genai
from datetime import datetime, timedelta

# Lazy-load client to ensure env vars are loaded first
_client = None

def _get_client():
    """Get or create the Gemini client"""
    global _client
    if _client is None:
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "GOOGLE_GEMINI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        _client = genai.Client(api_key=api_key)
    return _client

def parse_message_to_events(message_text):
    """
    Use Google Gemini to parse natural language message into structured calendar events.

    Args:
        message_text (str): Raw text from Discord message

    Returns:
        list: List of event dictionaries with structure:
            {
                'summary': str,
                'description': str (optional),
                'start': datetime,
                'end': datetime,
                'location': str (optional)
            }
    """

    # Get current date and time for context
    now = datetime.now()
    current_context = f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    # Craft prompt for Gemini
    prompt = f"""
{current_context}

You are Alfred's calendar event parser. Extract calendar event details from natural language messages.
The user may address you as "Alfred" or use conversational language - focus on extracting the actual event details.

Message: "{message_text}"

Return ONLY a valid JSON array with this exact structure (no markdown, no explanation, no extra text):
[
  {{
    "summary": "Brief, clear event title",
    "description": "Detailed description of what will be discussed or done (optional)",
    "start_datetime": "YYYY-MM-DD HH:MM",
    "end_datetime": "YYYY-MM-DD HH:MM",
    "location": "Location if mentioned (optional)",
    "recurrence": "RRULE if recurring (optional)",
    "reminders": {{
      "useDefault": false,
      "overrides": [
        {{"method": "popup", "minutes": 60}}
      ]
    }} (optional - only if user mentions notifications/reminders)
  }}
]

IMPORTANT RULES FOR TITLES & DESCRIPTIONS:
- Create a brief, professional title (2-5 words)
- Put details/context in the description field, not the title
- Example: "Meeting about buying new phone" → title: "Phone Purchase Meeting", description: "Discuss buying a new phone"
- Example: "Standup with team to discuss project X" → title: "Team Standup", description: "Discuss project X progress"

RECURRING EVENTS:
- If user says "every Monday", "weekly", "daily", etc., add recurrence field
- RRULE format examples:
  - Daily: "RRULE:FREQ=DAILY"
  - Weekly on Monday: "RRULE:FREQ=WEEKLY;BYDAY=MO"
  - Every weekday: "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
  - Monthly: "RRULE:FREQ=MONTHLY"
  - With end date: "RRULE:FREQ=WEEKLY;UNTIL=20260301T000000Z"

REMINDERS/NOTIFICATIONS:
- If user mentions "remind me", "notification", "alert", extract the time
- Examples: "1 hour notification" → 60 minutes, "30 min reminder" → 30 minutes
- Default method is "popup" for notifications
- Only include reminders field if explicitly mentioned

LOCATION:
- Extract any mentioned location (office, zoom link, address, etc.)

TIME PARSING:
- Parse relative dates: "tomorrow", "next Monday", "Wednesday", "Friday", etc.
- Parse time ranges: "1-2" means 1:00 PM to 2:00 PM, "from 3-5" means 3:00 PM to 5:00 PM
- If time format is "1-2", assume PM unless it's clearly morning (like "9-10" = AM)
- Use 24-hour format for datetime fields (13:00 for 1 PM)

Examples:
"Meeting tomorrow at 3pm"
→ [{{"summary": "Meeting", "start_datetime": "2026-02-18 15:00", "end_datetime": "2026-02-18 16:00"}}]

"I have a meeting on Wednesday from 1-2 discussing buying a new phone with 1 hour notification"
→ [{{"summary": "Phone Purchase Meeting", "description": "Discuss buying a new phone", "start_datetime": "2026-02-19 13:00", "end_datetime": "2026-02-19 14:00", "reminders": {{"useDefault": false, "overrides": [{{"method": "popup", "minutes": 60}}]}}}}]

"Team standup every Monday at 9am"
→ [{{"summary": "Team Standup", "start_datetime": "2026-02-17 09:00", "end_datetime": "2026-02-17 09:30", "recurrence": "RRULE:FREQ=WEEKLY;BYDAY=MO"}}]

"Doctor appointment next Tuesday at 10am at 123 Main St with 30 min reminder"
→ [{{"summary": "Doctor Appointment", "start_datetime": "2026-02-18 10:00", "end_datetime": "2026-02-18 11:00", "location": "123 Main St", "reminders": {{"useDefault": false, "overrides": [{{"method": "popup", "minutes": 30}}]}}}}]

Now parse the message above and return ONLY the JSON array.
"""

    try:
        # Call Gemini API
        client = _get_client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        response_text = response.text.strip()

        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith('```json'):
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif response_text.startswith('```'):
            response_text = response_text.split('```')[1].split('```')[0].strip()

        # Parse JSON response
        events_raw = json.loads(response_text)

        print(f"✅ Gemini parsed {len(events_raw)} event(s)")
        if events_raw:
            print(f"📅 Raw events: {events_raw}")

        # Convert to proper format
        events = []
        for event in events_raw:
            try:
                parsed_event = {
                    'summary': event.get('summary', 'Untitled Event'),
                    'start': datetime.strptime(event['start_datetime'], '%Y-%m-%d %H:%M'),
                    'end': datetime.strptime(event['end_datetime'], '%Y-%m-%d %H:%M'),
                }

                # Add optional fields
                if event.get('description'):
                    parsed_event['description'] = event['description']
                if event.get('location'):
                    parsed_event['location'] = event['location']
                if event.get('recurrence'):
                    parsed_event['recurrence'] = event['recurrence']
                if event.get('reminders'):
                    parsed_event['reminders'] = event['reminders']

                events.append(parsed_event)
            except (KeyError, ValueError) as e:
                print(f"Error parsing event: {str(e)}")
                continue

        return events

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {str(e)}")
        print(f"📝 Raw response from Gemini:")
        print(response_text)
        return []
    except Exception as e:
        print(f"❌ Error calling Gemini API: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
