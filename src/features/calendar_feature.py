"""
Calendar Feature - Converts natural language to Google Calendar events.

This is the first feature of the assistant bot. More features can be added
in separate modules following the same pattern.
"""

import os
from google import genai
from services.gemini_parser import parse_message_to_events
from services.calendar_service import create_calendar_event, search_events, modify_event, get_read_service

# Lazy-load Gemini client
_client = None

def _get_client():
    """Get or create the Gemini client"""
    global _client
    if _client is None:
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY not found in environment variables")
        _client = genai.Client(api_key=api_key)
    return _client

class CalendarFeature:
    """
    Handles calendar-related requests.
    """

    def __init__(self):
        self.name = "Calendar"
        self.description = "Create and manage Google Calendar events"

    def get_capabilities(self):
        """
        Describe what this feature can do for the AI router.

        Returns:
            str: Detailed description of capabilities
        """
        return """
This feature can:
- Create calendar events from natural language descriptions
- Modify/update existing calendar events (rename, change time, etc.)
- View your schedule and upcoming events
- Schedule meetings, appointments, and reminders
- Handle time-based requests (dates, times, durations)
- Add events to Google Calendar
- Search and update recurring events

Examples of what this feature handles:

Creating events:
- "Meeting tomorrow at 3pm"
- "Lunch with Sarah on Friday at noon for 2 hours"
- "Doctor appointment next Tuesday at 10am"
- "Schedule a call with John next Monday at 2:30pm"
- "Team standup every weekday at 9am"

Modifying events:
- "Rename all 'office hours' events to 'tutor hours'"
- "Change the title of office hours to tutor hours"
- "Update my team meeting to start at 3pm instead"
- "Move tomorrow's lunch to 1pm"
- "Change location of dentist appointment to downtown office"

Viewing schedule:
- "What's on my schedule today?"
- "What do I have tomorrow?"
- "Show me my events this week"
- "What's coming up?"
- "Do I have anything scheduled for Friday?"

Keywords that indicate this feature: meeting, appointment, schedule, calendar, event, book, reserve, remind (when time-based), rename, change, update, modify, move, what's on, upcoming
        """.strip()


    async def handle(self, message, message_text, context=None):
        """
        Process a calendar-related request.

        Args:
            message: Discord message object
            message_text (str): The user's message text
            context (list): Optional conversation context [(timestamp, role, message), ...]

        Returns:
            str: Response to send back to the user
        """
        try:
            # Use AI to parse the calendar request and determine action
            parsed_request = await self._parse_calendar_request(message_text, context)

            if not parsed_request:
                return (
                    "I couldn't understand your calendar request. "
                    "Try something like: 'Meeting tomorrow at 3pm' or 'Rename office hours to tutor hours'"
                )

            # Handle based on action type
            if parsed_request['action'] == 'modify':
                return await self._handle_modification(
                    parsed_request['search_query'],
                    parsed_request['updates']
                )
            elif parsed_request['action'] == 'view':
                return await self._handle_view_schedule(
                    parsed_request.get('start_date'),
                    parsed_request.get('end_date')
                )
            elif parsed_request['action'] == 'create':
                return await self._handle_creation(parsed_request['events'])
            else:
                return (
                    "I couldn't understand your calendar request. "
                    "Try creating an event ('Meeting tomorrow at 3pm'), "
                    "viewing your schedule ('What's on my calendar today?'), "
                    "or modifying an event ('Rename office hours to tutor hours')"
                )

        except Exception as e:
            print(f"Error in calendar feature: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"An error occurred while processing your calendar request: {str(e)}"

    async def _parse_calendar_request(self, message_text, context=None):
        """
        Use AI to parse calendar request and determine action (create or modify).

        Args:
            message_text: The user's current message
            context: Recent conversation history

        Returns:
            dict: Parsed request with action and relevant data, or None if parsing fails
        """
        try:
            from datetime import datetime
            import json

            client = _get_client()
            now = datetime.now()
            current_context = f"Current date and time: {now.strftime('%A, %Y-%m-%d %H:%M:%S')} (Today is {now.strftime('%A')})"

            # Format conversation context
            context_str = ""
            if context:
                context_str = "\nRecent conversation:\n"
                for timestamp, role, msg in context:
                    role_label = "User" if role == "user" else "Alfred"
                    context_str += f"{role_label}: {msg}\n"
                context_str += "\n"

            prompt = f"""
{current_context}
{context_str}

You are Alfred's unified calendar request parser. Analyze the user's message and determine if they want to CREATE a new event or MODIFY an existing event.

User message: "{message_text}"

Use the conversation context above to understand references like "it", "them", "that event", etc.
If the user refers to something mentioned earlier, use that information.

Based on the meaning of the message, return ONLY valid JSON (no markdown, no explanation):

FOR VIEWING SCHEDULE (asking what's on the calendar):
{{
  "action": "view",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}}

FOR EVENT CREATION (scheduling new events):
{{
  "action": "create",
  "events": [
    {{
      "summary": "Brief, clear event title",
      "description": "Detailed description (optional)",
      "start_datetime": "YYYY-MM-DD HH:MM",
      "end_datetime": "YYYY-MM-DD HH:MM",
      "location": "Location if mentioned (optional)",
      "recurrence": "RRULE if recurring (optional)",
      "reminders": {{
        "useDefault": false,
        "overrides": [{{"method": "popup", "minutes": 60}}]
      }} (optional)
    }}
  ]
}}

FOR EVENT MODIFICATION (changing existing events):
{{
  "action": "modify",
  "search_query": "what to search for (event name/keywords)",
  "updates": {{
    "summary": "new title (if renaming)",
    "description": "new description (if changing)",
    "location": "new location (if changing)",
    "reminders": {{
      "useDefault": false,
      "overrides": [{{"method": "popup", "minutes": 60}}]
    }} (if adding/changing reminders)
  }}
}}

VIEW EXAMPLES:
"What's on my schedule today?"
→ {{"action": "view", "start_date": "2026-02-17", "end_date": "2026-02-17"}}

"What do I have tomorrow?"
→ {{"action": "view", "start_date": "2026-02-18", "end_date": "2026-02-18"}}

"Show me my events this week"
→ {{"action": "view", "start_date": "2026-02-17", "end_date": "2026-02-23"}}

CREATION EXAMPLES:
"Meeting tomorrow at 3pm"
→ {{"action": "create", "events": [{{"summary": "Meeting", "start_datetime": "2026-02-18 15:00", "end_datetime": "2026-02-18 16:00"}}]}}

"Lunch with Sarah Friday at noon with 1 hour notification"
→ {{"action": "create", "events": [{{"summary": "Lunch with Sarah", "start_datetime": "2026-02-21 12:00", "end_datetime": "2026-02-21 13:00", "reminders": {{"useDefault": false, "overrides": [{{"method": "popup", "minutes": 60}}]}}}}]}}

MODIFICATION EXAMPLES:
"Rename office hours to tutor hours"
→ {{"action": "modify", "search_query": "office hours", "updates": {{"summary": "Tutor Hours"}}}}

"Add a 1 hour notification to CSE 127 makeup office hours"
→ {{"action": "modify", "search_query": "CSE 127 makeup office hours", "updates": {{"reminders": {{"useDefault": false, "overrides": [{{"method": "popup", "minutes": 60}}]}}}}}}

"Change team meeting location to Zoom"
→ {{"action": "modify", "search_query": "team meeting", "updates": {{"location": "Zoom"}}}}

IMPORTANT GUIDELINES:
- VIEW: User is asking what events are scheduled ("what's on...", "what do I have...", "show me...")
- CREATE: User is scheduling something new ("meeting at...", "I have...", "schedule...")
- MODIFY: User is changing something existing ("rename...", "change...", "add notification to...", "update...")
- **CRITICAL**: Calculate dates relative to CURRENT date/time provided above
  - If today is Tuesday, then "Thursday" = add 2 days
  - If today is Tuesday, then "next Tuesday" = add 7 days
  - Always count from the current day of week shown above
- For CREATE: Parse dates/times relative to current date
- For CREATE: Use 24-hour format (13:00 for 1 PM)
- For CREATE: Create brief titles, put details in description
- For MODIFY: Only include fields being changed in "updates"
- Reminder minutes: "1 hour" = 60, "30 min" = 30, "15 minutes" = 15
- Recurrence format: MUST start with "RRULE:" prefix (e.g., "RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20260331T235959Z")

Now parse the message and return ONLY the JSON.
            """.strip()

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            response_text = response.text.strip()

            # Clean up response (remove markdown if present)
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # Parse JSON
            parsed = json.loads(response_text)

            action = parsed.get('action')
            print(f"📋 Parsed calendar request: action={action}")

            # Log additional details for debugging
            if action == 'view':
                print(f"   → Start date: {parsed.get('start_date')}")
                print(f"   → End date: {parsed.get('end_date')}")

            return parsed

        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {str(e)}")
            print(f"📝 Raw response: {response_text}")
            return None
        except Exception as e:
            print(f"❌ Error parsing calendar request: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _handle_creation(self, events_data):
        """Handle creating new calendar events"""
        try:
            from datetime import datetime

            # Convert event data to proper format
            events = []
            for event in events_data:
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

            if not events:
                return "I couldn't parse the event details. Please try again."

            # Create calendar events
            created_events = []
            for event_data in events:
                try:
                    event = create_calendar_event(event_data)
                    created_events.append(event)
                except Exception as e:
                    print(f"Error creating event: {str(e)}")
                    continue

            # Build response
            if created_events:
                if len(created_events) == 1:
                    event = created_events[0]

                    # Format times in readable format
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                    end_dt = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))

                    # Format: "Mon, Feb 17 at 12:00 PM → 3:00 PM"
                    if start_dt.date() == end_dt.date():
                        time_str = f"{start_dt.strftime('%a, %b %d at %-I:%M %p')} → {end_dt.strftime('%-I:%M %p')}"
                    else:
                        time_str = f"{start_dt.strftime('%a, %b %d at %-I:%M %p')} → {end_dt.strftime('%a, %b %d at %-I:%M %p')}"

                    response = f"✓ **{event['summary']}**\n"
                    response += f"📅 {time_str}"

                    # Add recurrence info if present (show early for visibility)
                    if event.get('recurrence'):
                        response += f"\n🔁 Recurring"

                    # Add description if present
                    if event.get('description'):
                        response += f"\n📝 Description: {event['description']}"

                    # Add location if present
                    if event.get('location'):
                        response += f"\n📍 Location: {event['location']}"

                    # Add reminder info if present
                    if event.get('reminders') and not event['reminders'].get('useDefault'):
                        reminders = event['reminders'].get('overrides', [])
                        if reminders:
                            reminder_times = [f"{r['minutes']}min" for r in reminders]
                            response += f"\n🔔 Reminders: {', '.join(reminder_times)}"

                    return response
                else:
                    # Multiple events - show details for each
                    from datetime import datetime
                    event_details = []
                    for event in created_events:
                        start_dt = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                        end_dt = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))

                        # Format time
                        if start_dt.date() == end_dt.date():
                            time_str = f"{start_dt.strftime('%a, %b %d at %-I:%M %p')} → {end_dt.strftime('%-I:%M %p')}"
                        else:
                            time_str = f"{start_dt.strftime('%a, %b %d at %-I:%M %p')} → {end_dt.strftime('%a, %b %d at %-I:%M %p')}"

                        detail = f"• **{event['summary']}**\n  📅 {time_str}"

                        # Add recurring indicator
                        if event.get('recurrence'):
                            detail += "\n  🔁 Recurring"

                        # Add location if present
                        if event.get('location'):
                            detail += f"\n  📍 {event['location']}"

                        event_details.append(detail)

                    event_list = "\n\n".join(event_details)
                    return f"✓ Created {len(created_events)} events:\n\n{event_list}"
            else:
                return "Sorry, I couldn't create any calendar events. Please try again."

        except Exception as e:
            print(f"Error in event creation: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"An error occurred while creating events: {str(e)}"

    def _format_context(self, context):
        """Format conversation context for AI prompts"""
        if not context:
            return ""

        formatted = "\nRecent conversation:\n"
        for timestamp, role, msg in context:
            role_label = "User" if role == "user" else "Alfred"
            formatted += f"{role_label}: {msg}\n"
        return formatted + "\n"

    async def _handle_modification(self, search_query, updates):
        """Handle requests to modify existing calendar events (data already parsed by AI)"""
        try:
            if not search_query:
                return "I couldn't understand what events you want to modify. Please be more specific."

            # Search for matching events
            matching_events = search_events(search_query)

            if not matching_events:
                return f"I couldn't find any events matching '{search_query}'."

            # Modify all matching events
            modified_count = 0
            modified_events = []
            is_recurring = False
            for event in matching_events:
                try:
                    modify_event(event['id'], updates)
                    modified_count += 1
                    # Get the updated event title and check if recurring
                    event_title = updates.get('summary', event.get('summary', 'Untitled'))
                    modified_events.append(event_title)
                    if event.get('recurrence'):
                        is_recurring = True
                except Exception as e:
                    print(f"Error modifying event {event.get('summary')}: {str(e)}")
                    continue

            # Build response
            if modified_count > 0:
                # Build update description
                update_lines = []
                if 'summary' in updates:
                    update_lines.append(f"📝 Title: **{updates['summary']}**")
                if 'description' in updates:
                    update_lines.append(f"📝 Description: {updates['description']}")
                if 'location' in updates:
                    update_lines.append(f"📍 Location: {updates['location']}")
                if 'reminders' in updates:
                    reminder_minutes = updates['reminders'].get('overrides', [{}])[0].get('minutes', 0)
                    update_lines.append(f"🔔 Reminder: {reminder_minutes} min before")

                update_text = "\n".join(update_lines)

                # Add recurring indicator if applicable
                recurring_text = "\n🔁 Recurring" if is_recurring else ""

                if modified_count == 1:
                    event_name = modified_events[0]
                    return f"✓ Modified **{event_name}**{recurring_text}\n{update_text}"
                else:
                    return f"✓ Modified {modified_count} events{recurring_text}\n{update_text}"
            else:
                return "I found matching events but couldn't modify them. Please try again."

        except Exception as e:
            print(f"Error in modification handler: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"An error occurred while modifying events: {str(e)}"

    async def _handle_view_schedule(self, start_date, end_date):
        """Handle requests to view schedule (uses readonly service to read ALL calendars)"""
        try:
            from datetime import datetime, timedelta

            if not start_date or not end_date:
                return "I couldn't understand the date range for viewing your schedule."

            # Get readonly service (can read all calendars)
            service = get_read_service()

            # Parse dates from AI-provided format (YYYY-MM-DD)
            # Use local timezone (PST/PDT) for proper date boundaries
            from zoneinfo import ZoneInfo

            # Get local timezone (defaulting to America/Los_Angeles)
            # TODO: Make this configurable per user or auto-detect
            local_tz = ZoneInfo('America/Los_Angeles')

            # Create start and end times in local timezone
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=local_tz)
            # For end date, go to the END of the day (next day at 00:00 local time)
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=local_tz)
            end_dt = end_dt + timedelta(days=1)  # Go to start of next day in local timezone

            # Generate friendly label for date range
            if start_date == end_date:
                # Single day
                if start_dt.date() == datetime.now().date():
                    range_label = "today"
                elif start_dt.date() == (datetime.now() + timedelta(days=1)).date():
                    range_label = "tomorrow"
                else:
                    range_label = start_dt.strftime('%A, %B %d')
            else:
                # Date range
                range_label = f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}"

            # Get list of all calendars
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])

            print(f"📅 Found {len(calendars)} calendars to query")
            print(f"📅 Date range: {start_dt.isoformat()} to {end_dt.isoformat()}")

            # Fetch events from ALL calendars and combine them
            all_events = []
            for calendar in calendars:
                calendar_id = calendar['id']
                calendar_name = calendar.get('summary', 'Unknown')

                try:
                    # Send timezone-aware timestamps (no 'Z' needed, isoformat includes timezone)
                    events_result = service.events().list(
                        calendarId=calendar_id,
                        timeMin=start_dt.isoformat(),
                        timeMax=end_dt.isoformat(),
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()

                    events = events_result.get('items', [])

                    # Tag each event with its calendar name for context
                    for event in events:
                        event['_calendar_name'] = calendar_name
                        all_events.append(event)

                    print(f"  • {calendar_name}: {len(events)} events")

                except Exception as e:
                    print(f"  ⚠️ Skipping calendar '{calendar_name}': {str(e)}")
                    continue

            if not all_events:
                return f"You have no events scheduled for {range_label}."

            # Sort all events: all-day events first, then by start time
            def get_event_sort_key(event):
                """Get sortable key for event (all-day events first, then by time)"""
                from datetime import timezone
                start = event['start'].get('dateTime', event['start'].get('date'))

                if 'T' in start:  # datetime event
                    # Return tuple: (1, datetime) - regular events sort after all-day
                    return (1, datetime.fromisoformat(start.replace('Z', '+00:00')))
                else:  # all-day event
                    # Return tuple: (0, datetime) - all-day events sort first
                    naive_dt = datetime.strptime(start, '%Y-%m-%d')
                    return (0, naive_dt.replace(tzinfo=timezone.utc))

            all_events.sort(key=get_event_sort_key)

            # Deduplicate events (same summary + same start time = duplicate)
            seen = set()
            unique_events = []
            for event in all_events:
                event_key = (event.get('summary', 'Untitled'), event['start'].get('dateTime', event['start'].get('date')))
                if event_key not in seen:
                    seen.add(event_key)
                    unique_events.append(event)
                else:
                    print(f"  🔄 Skipping duplicate: {event.get('summary')} at {event['start'].get('dateTime', event['start'].get('date'))}")

            all_events = unique_events

            # Format events for display (with date filtering)
            event_lines = []
            target_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            print(f"📅 Filtering events for target date: {target_date}")
            print(f"📅 Processing {len(all_events)} events after deduplication:")

            for event in all_events:
                summary = event.get('summary', 'Untitled')
                start = event['start'].get('dateTime', event['start'].get('date'))
                calendar_name = event.get('_calendar_name', '')

                # Parse and format time
                if 'T' in start:  # datetime
                    start_dt_event = datetime.fromisoformat(start.replace('Z', '+00:00'))

                    # DEBUG: Log the actual event date/time
                    print(f"   📌 {summary}: {start_dt_event.isoformat()}")
                    print(f"      Calendar: {calendar_name}")
                    print(f"      Event date: {start_dt_event.date()}, Target: {target_date}")

                    # Check if event is actually on the requested date (using local date)
                    event_date = start_dt_event.date()

                    if event_date != target_date:
                        print(f"      ⚠️  SKIPPING - Date mismatch!")
                        continue

                    print(f"      ✅ INCLUDED")
                    time_str = start_dt_event.strftime('%-I:%M %p')
                else:  # all-day event
                    start_dt_event = datetime.strptime(start, '%Y-%m-%d')
                    print(f"   📌 {summary}: {start} (all-day)")
                    print(f"      Calendar: {calendar_name}")
                    print(f"      ✅ INCLUDED (all-day)")
                    time_str = "All day"

                # Add location if present
                location = event.get('location', '')
                location_str = f" @ {location}" if location else ""

                event_lines.append(f"• {time_str}: **{summary}**{location_str}")

            if not event_lines:
                return f"You have no events scheduled for {range_label}."

            events_text = "\n".join(event_lines)
            header = f"📅 Your schedule for {range_label}:\n\n"

            return header + events_text

        except ValueError as e:
            print(f"Error parsing dates: {str(e)}")
            return "I couldn't parse the date range. Please try again."
        except Exception as e:
            print(f"Error viewing schedule: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"An error occurred while viewing your schedule: {str(e)}"
