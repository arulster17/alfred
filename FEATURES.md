# Adding New Features to the AI Assistant Bot

The bot uses **AI-powered intent routing** to intelligently understand what users want and route to the appropriate feature.

## Architecture Overview

```
User Message
    ↓
Discord Bot
    ↓
AI Intent Router (Gemini)
    ↓
Analyzes: "What is the user trying to do?"
    ↓
Selects Best Feature
    ↓
Feature Handles Request
    ↓
Response to User
```

## How It Works

Instead of keyword matching, the bot uses Google Gemini to:
1. Understand the user's intent
2. Compare against all available features and their capabilities
3. Route to the best matching feature
4. Handle the request intelligently

**This means users can phrase requests ANY way they want - the AI figures it out!**

## Current Features

### 📅 Calendar Feature
- **Location:** `src/features/calendar_feature.py`
- **Purpose:** Create Google Calendar events from natural language
- **Examples:**
  - "Meeting tomorrow at 3pm"
  - "Schedule lunch with Sarah on Friday at noon"
  - "Add dentist appointment next Tuesday"

## How to Add a New Feature

### Step 1: Create a New Feature Module

Create a new file in `src/features/` (e.g., `reminder_feature.py`):

```python
"""
Reminder Feature - Set time-based reminders
"""

class ReminderFeature:
    """
    Handles reminder-related requests.
    """

    def __init__(self):
        self.name = "Reminders"
        self.description = "Set time-based reminders and notifications"

    def get_capabilities(self):
        """
        Tell the AI router what this feature can do.
        The more detailed and specific, the better the routing!
        """
        return """
This feature can:
- Set reminders for specific times
- Notify users about tasks or events
- Schedule one-time or recurring reminders

Examples of what this feature handles:
- "Remind me to call mom in 2 hours"
- "Set a reminder for tomorrow at 9am to take medication"
- "Notify me in 30 minutes"
- "Remind me every Monday at 8am to submit report"

Keywords that indicate this feature: remind, reminder, notify, notification, alert, nudge
        """.strip()

    def can_handle(self, message_text):
        """
        Fallback method if AI routing fails.
        Return True if this feature should handle the message.
        """
        keywords = ["remind", "reminder", "notify", "alert"]
        lower_text = message_text.lower()
        return any(keyword in lower_text for keyword in keywords)

    async def handle(self, message, message_text):
        """
        Process the reminder request.

        Args:
            message: Discord message object
            message_text (str): The user's message text

        Returns:
            str: Response to send back to the user
        """
        try:
            # Your feature logic here
            # Example: parse reminder time, store it, schedule notification

            # For now, just a placeholder
            return "✓ Reminder feature coming soon!"

        except Exception as e:
            print(f"Error in reminder feature: {str(e)}")
            return f"An error occurred: {str(e)}"
```

### Step 2: Register the Feature

Edit `src/services/discord_handler.py` in the `_load_features()` method:

```python
def _load_features(self):
    """Load all available features and register them with the AI router"""
    # Existing features
    calendar = CalendarFeature()
    self.router.register_feature(calendar)

    # Add your new feature
    from features.reminder_feature import ReminderFeature
    reminder = ReminderFeature()
    self.router.register_feature(reminder)

    print(f"Loaded {len(self.router.features)} features:")
    for feature in self.router.features:
        print(f"  - {feature.name}: {feature.description}")
```

### Step 3: Test Your Feature

Run the bot and test your new feature:
```bash
cd src
python bot.py
```

The AI will automatically learn to route to your feature!

Test with messages like:
- "Remind me to call mom tomorrow"
- "Set a reminder for 5pm"
- "Notify me in 1 hour"

## Feature Interface

Every feature must implement:

### Required Methods

#### `__init__(self)`
Initialize with:
- `self.name` - Display name (e.g., "Reminders")
- `self.description` - Short description (e.g., "Set time-based reminders")

#### `get_capabilities(self) -> str`
**Most important method!** Returns a detailed description of what this feature does.

The AI uses this to understand when to route to your feature.

**Tips for writing good capabilities:**
- Be specific and detailed
- Include lots of examples
- List keywords that indicate this feature
- Describe edge cases or special handling
- The more context you give, the better the AI routing!

Example:
```python
def get_capabilities(self):
    return """
This feature can:
- [List what it can do]

Examples:
- "[Example user message 1]"
- "[Example user message 2]"

Keywords: keyword1, keyword2, keyword3
    """.strip()
```

#### `async handle(self, message, message_text) -> str`
Process the request and return a response string.

**Parameters:**
- `message` - Discord message object
- `message_text` - Clean message text

**Returns:**
- String response to send to the user

#### `can_handle(self, message_text) -> bool` (Optional)
Fallback for keyword-based routing if AI fails.

**Only called if AI routing doesn't work - not normally used!**

## Example Features

### Email Feature

```python
# src/features/email_feature.py

class EmailFeature:
    def __init__(self):
        self.name = "Email"
        self.description = "Send and manage emails"

    def get_capabilities(self):
        return """
This feature can:
- Send emails to contacts
- Draft email messages
- Handle email-related requests

Examples:
- "Email John about the meeting tomorrow"
- "Send an email to sarah@example.com saying I'll be late"
- "Draft an email to the team about the project update"

Keywords: email, send email, message, contact, draft
        """.strip()

    def can_handle(self, message_text):
        keywords = ["email", "send email", "mail"]
        return any(kw in message_text.lower() for kw in keywords)

    async def handle(self, message, message_text):
        # Use AI to parse: recipient, subject, body
        # Send email via Gmail API or SMTP
        return "✓ Email sent!"
```

### Weather Feature

```python
# src/features/weather_feature.py
import requests

class WeatherFeature:
    def __init__(self):
        self.name = "Weather"
        self.description = "Get weather forecasts and current conditions"

    def get_capabilities(self):
        return """
This feature can:
- Get current weather for locations
- Provide weather forecasts
- Answer weather-related questions

Examples:
- "What's the weather like today?"
- "Weather in San Francisco"
- "Will it rain tomorrow?"
- "Temperature in New York"

Keywords: weather, temperature, forecast, rain, snow, sunny, cloudy
        """.strip()

    def can_handle(self, message_text):
        keywords = ["weather", "temperature", "forecast", "rain"]
        return any(kw in message_text.lower() for kw in keywords)

    async def handle(self, message, message_text):
        # Extract location using AI
        # Call weather API
        # Return formatted weather info
        return "🌤️ Weather: 72°F, Sunny"
```

### Todo List Feature

```python
# src/features/todo_feature.py

class TodoFeature:
    def __init__(self):
        self.name = "Todo List"
        self.description = "Manage tasks and todo items"
        self.todos = {}  # Store per-user todos

    def get_capabilities(self):
        return """
This feature can:
- Add tasks to a todo list
- List current todos
- Mark tasks as complete
- Manage personal task lists

Examples:
- "Add buy milk to my todo list"
- "Add task: finish report"
- "Show my todos"
- "List my tasks"
- "Mark first task as done"

Keywords: todo, task, checklist, add task, list tasks
        """.strip()

    def can_handle(self, message_text):
        keywords = ["todo", "task", "checklist"]
        return any(kw in message_text.lower() for kw in keywords)

    async def handle(self, message, message_text):
        user_id = message.author.id

        # Initialize user's todo list
        if user_id not in self.todos:
            self.todos[user_id] = []

        # Use AI to determine action: add, list, complete, etc.
        # For simplicity, basic keyword checking here
        if "add" in message_text.lower():
            task = message_text.split("add", 1)[1].strip()
            self.todos[user_id].append(task)
            return f"✓ Added: {task}"
        elif "list" in message_text.lower() or "show" in message_text.lower():
            if not self.todos[user_id]:
                return "Your todo list is empty!"
            tasks = "\n".join([f"{i+1}. {t}" for i, t in enumerate(self.todos[user_id])])
            return f"**Your Todos:**\n{tasks}"

        return "Try: 'add task: [task]' or 'list todos'"
```

## AI Routing Details

### How the AI Router Works

1. **Feature Registration:** Each feature registers with the router, providing its capabilities
2. **User Message:** User sends a message to the bot
3. **AI Analysis:** Router sends all feature capabilities + user message to Gemini
4. **Intent Classification:** Gemini determines which feature best matches the user's intent
5. **Confidence Check:** If confidence > 60%, route to that feature
6. **Execution:** Selected feature handles the request

### Routing Prompt

The router sends this to Gemini:
```
User message: "[user's message]"

Available features:
[
  {
    "name": "Calendar",
    "description": "Create calendar events",
    "capabilities": "[detailed capabilities]"
  },
  {
    "name": "Email",
    "description": "Send emails",
    "capabilities": "[detailed capabilities]"
  }
]

Which feature should handle this?
```

Gemini responds:
```json
{
  "feature_index": 0,
  "confidence": 0.95,
  "reasoning": "User wants to schedule an event"
}
```

### Customizing AI Routing

You can modify `src/services/intent_router.py` to:
- Adjust confidence threshold (currently 0.6)
- Change the routing prompt
- Add multi-feature routing (one message, multiple features)
- Implement fallback strategies

## Tips for Building Features

1. **Write detailed capabilities** - The AI is only as good as the info you give it
2. **Include lots of examples** - Help the AI understand edge cases
3. **Use external services** - Leverage APIs for weather, news, translation, etc.
4. **Keep features focused** - One feature = one type of task
5. **Handle errors gracefully** - Always return user-friendly error messages
6. **Use AI for parsing** - Gemini is great for extracting structured data from natural language
7. **Test thoroughly** - Try different phrasings to ensure routing works

## Advanced: Using AI Within Features

Features can also use Gemini for internal processing:

```python
async def handle(self, message, message_text):
    # Use Gemini to extract structured data
    prompt = f"""
    Extract the email details from this message:
    "{message_text}"

    Return JSON with: recipient, subject, body
    """

    response = genai.generate_content(prompt)
    data = json.loads(response.text)

    # Send email with extracted data
    send_email(data['recipient'], data['subject'], data['body'])
    return "✓ Email sent!"
```

## Ideas for Future Features

- 📝 **Notes** - Save and retrieve notes
- ⏰ **Reminders** - Time-based notifications
- ✅ **Todo Lists** - Task management
- 🌤️ **Weather** - Weather forecasts
- 📰 **News** - News summaries
- 💱 **Currency** - Currency conversion
- 🌍 **Translation** - Translate text
- 📊 **Habit Tracker** - Track daily habits
- 🎵 **Music** - Control Spotify
- 📧 **Email** - Send/read emails
- 🔍 **Web Search** - Search and summarize web results
- 📁 **File Management** - Manage files/documents
- 🧮 **Calculator** - Perform calculations
- 🎲 **Random** - Random number/choice generation

The AI-powered architecture means you can add ANY feature and the bot will automatically learn to route to it!
