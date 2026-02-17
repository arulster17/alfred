"""
Calendar Feature - Converts natural language to Google Calendar events.

This is the first feature of the assistant bot. More features can be added
in separate modules following the same pattern.
"""

import os
from google import genai
from services.gemini_parser import parse_message_to_events
from services.calendar_service import create_calendar_event, search_events, modify_event

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

Keywords that indicate this feature: meeting, appointment, schedule, calendar, event, book, reserve, remind (when time-based), rename, change, update, modify, move
        """.strip()

    def can_handle(self, message_text):
        """
        Fallback method for keyword-based routing if AI routing fails.

        Args:
            message_text (str): The user's message

        Returns:
            bool: True if this feature should handle the message
        """
        keywords = ["meeting", "appointment", "schedule", "calendar", "event",
                   "lunch", "dinner", "call", "tomorrow", "today", "next week"]
        lower_text = message_text.lower()
        return any(keyword in lower_text for keyword in keywords)

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
            else:  # action == 'create'
                return await self._handle_creation(parsed_request['events'])

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
            current_context = f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

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
- CREATE: User is scheduling something new ("meeting at...", "I have...", "schedule...")
- MODIFY: User is changing something existing ("rename...", "change...", "add notification to...", "update...")
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

            print(f"📋 Parsed calendar request: action={parsed.get('action')}")
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
