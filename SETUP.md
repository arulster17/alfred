# Setup Guide - AI Assistant Bot (Discord)

This guide will walk you through setting up an AI-powered Discord assistant bot.

**What this bot does:**
- Uses AI to understand what you want (natural language)
- Currently supports: Creating Google Calendar events
- Designed to be easily extended with more features (email, reminders, todos, weather, etc.)

The bot uses Google Gemini AI to intelligently route your requests to the appropriate feature.

## Prerequisites

- Python 3.11+
- A Google account
- A Discord account
- Basic command line knowledge

---

## Step 1: Install Dependencies

```bash
cd auto-calendar
pip install -r requirements.txt
```

---

## Step 2: Google Gemini API Setup (FREE)

**Why needed:** The bot uses Gemini AI for two things:
1. Understanding your intent (routing messages to the right feature)
2. Parsing natural language into calendar events

**Setup:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key" or "Create API Key"
3. Copy your API key
4. Keep this for later (you'll add it to `.env`)

**Cost:** FREE tier available
**Model used:** gemini-2.0-flash
**Note:**
- Each message you send uses 1-2 requests (one for routing, one for parsing if it's a calendar event)
- Free tier quotas vary by model - check https://ai.google.dev/pricing for current limits
- If you hit rate limits, wait for quota reset or consider upgrading

---

## Step 3: Google Calendar API Setup (FREE)

⚠️ **IMPORTANT:** Alfred uses **dual authentication** for security. You need to set up TWO OAuth credentials:
1. **User credentials** (readonly) - Read all calendars
2. **Bot credentials** (write) - Write to bot calendar only

This ensures Alfred can VIEW your work/personal calendars but can ONLY CREATE/MODIFY events in a dedicated bot calendar.

**👉 Follow the detailed guide:** [BOT_CALENDAR_SETUP.md](BOT_CALENDAR_SETUP.md)

**Quick summary:**
1. Create a dedicated "Alfred Bot" calendar
2. Set up two OAuth credentials (user + bot)
3. Share bot calendar with bot identity
4. Update .env with bot calendar ID

**Why this approach:**
- Alfred can read from ALL calendars (for "what's my schedule")
- Alfred can only write to bot calendar (physical ACL isolation)
- Your primary calendar is protected even if code has bugs

**Cost:** FREE

---

## Step 4: Create Discord Bot (FREE)

### 4.1 Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it something like "AI Assistant" or "My Assistant Bot" (or whatever you like)
4. Click "Create"

### 4.2 Create Bot User

1. In your application, go to "Bot" tab (left sidebar)
2. Click "Add Bot" → "Yes, do it!"
3. Under "Token", click "Reset Token" and copy it
   - **IMPORTANT:** Save this token - you can't see it again!
4. Scroll down to "Privileged Gateway Intents"
5. Enable these intents:
   - ✅ MESSAGE CONTENT INTENT (required to read messages)
   - ✅ DIRECT MESSAGES (required for DMs)
6. Click "Save Changes"

### 4.3 Add Bot to Access DMs

**Important:** Discord bots cannot be added as "friends" like users. To DM a bot, you need to add it somewhere first, then you can DM it.

**Easiest Method: Create a Private Server**
1. In Discord, click the "+" button on the left sidebar
2. Select "Create My Own" → "For me and my friends"
3. Name it something like "Personal Bot Server" (you'll be the only member)
4. Click "Create"

**Then Add Your Bot:**
1. Go to "OAuth2" → "URL Generator" (left sidebar) in Discord Developer Portal
2. Under "Scopes", select:
   - ✅ bot
3. Under "Bot Permissions", select:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
4. Copy the generated URL at the bottom
5. Paste it in your browser
6. Select your private server from the dropdown
7. Click "Authorize"

**Now You Can DM It:**
1. Go to your Discord
2. Click on your bot's name in your private server
3. Click "Message" or right-click → "Message"
4. Send a DM!

The bot will respond to your DMs even though it's technically in a server. You can ignore the server channel - just use DMs.

**Note:** You could also add it to any existing server you own/admin, but a private server keeps it cleaner.

**Cost:** FREE

---

## Step 5: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your credentials:
   ```
   DISCORD_BOT_TOKEN=your_actual_discord_bot_token
   GOOGLE_GEMINI_API_KEY=your_actual_gemini_key
   GOOGLE_CALENDAR_ID=primary
   ```

---

## Step 6: First Time Authentication (Google Calendar)

Run this once to authenticate with Google Calendar:

```bash
cd src
python -c "from services.calendar_service import get_calendar_service; get_calendar_service()"
```

This will:
- Open your browser
- Ask you to sign in to Google
- Request permission to manage your calendar
- Save credentials to `token.pickle`

**Important:** Click "Advanced" > "Go to [Your App Name] (unsafe)" if Google shows a warning (this is normal for personal projects not verified by Google).

---

## Step 7: Run the Bot Locally

```bash
cd src
python bot.py
```

You should see:
```
Starting Discord assistant bot...
Loaded 1 features:
  - Calendar: Create and manage Google Calendar events
AssistantBot#1234 has connected to Discord!
Bot is ready to receive messages
```

---

## Step 8: Test It!

The bot uses AI to understand your intent - you can phrase things naturally!

### Send a DM to the bot
1. Find your bot in Discord (you might need to refresh or check your DMs)
2. Click on it and send a DM:
   ```
   Meeting with John tomorrow at 3pm for 1 hour
   ```

The AI will:
1. Understand you want to create a calendar event
2. Route to the Calendar feature
3. Parse the event details
4. Create it in Google Calendar
5. Reply with confirmation

You should get a confirmation and see the event in your Google Calendar!

**Note:** The bot is configured to only respond to DMs. If you mention it in a server, it will respond, but it's designed primarily for personal DM use.

### More examples to try:

**Calendar events (various phrasings):**
- "Meeting tomorrow at 3pm"
- "Schedule a call with the team next Monday at 2pm"
- "Add dentist appointment on March 20th at 10am"
- "Book lunch with Sarah Friday noon"
- "Team standup next Monday at 9:30am for 30 minutes"

**The AI understands natural language - try phrasing things YOUR way!**

### Bot Commands:
- `!help` - Show help message and available features
- `!ping` - Check if bot is responsive
- `!features` - List all available features

### How to verify it's working:

In the terminal where the bot is running, you'll see:
```
AI Router selected: Calendar
```

This shows the AI understood your intent and routed to the Calendar feature!

---

## Step 9: Deploy to Production (FREE - 24/7 hosting)

Deploy the bot so it runs even when your laptop is closed!

### Option A: Fly.io (Recommended - FREE & Always-On)

**Why Fly.io:**
- ✅ Free tier: 3 small VMs (256MB RAM) forever
- ✅ Always-on, no spin-down (critical for reminders)
- ✅ Persistent storage included
- ✅ No credit card required for free tier

**Setup:**
1. Install Fly CLI: `brew install flyctl` (macOS) or see [docs](https://fly.io/docs/hands-on/install-flyctl/)
2. Sign up: `flyctl auth signup`
3. Create `fly.toml` in project root (Fly config file)
4. Deploy: `flyctl launch`
5. Set secrets:
   ```bash
   flyctl secrets set DISCORD_BOT_TOKEN=your_token
   flyctl secrets set GOOGLE_GEMINI_API_KEY=your_key
   flyctl secrets set GOOGLE_CALENDAR_ID=primary
   ```
6. Deploy: `flyctl deploy`

**Important for Fly.io:**
You'll need to handle Google Calendar authentication differently for cloud deployment:
- Run authentication locally first to generate `token.pickle`
- Upload it as part of deployment or mount as secret

### Option B: Render (Spins Down on Free Tier)

**⚠️ Warning:** Free tier spins down after 15min inactivity - will miss reminders!

Only use Render if you're on paid tier ($7/month).

1. Create account at [Render](https://render.com/)
2. Click "New" > "Web Service"
3. Connect GitHub repo
4. Configure build/start commands
5. Add environment variables

### Option C: Railway (No Free Tier)

**⚠️ Railway removed free tier** - now requires $5/month minimum with payment method.

Not recommended unless you want to pay.

### Option C: Keep Running Locally

If you want to keep your laptop running:
```bash
cd src
python bot.py
```

Keep this terminal open. Bot will run until you close it.

**For background process (macOS/Linux):**
```bash
cd src
nohup python bot.py > bot.log 2>&1 &
```

---

## Troubleshooting

### "No module named 'services'"
Make sure you're running from the `src/` directory:
```bash
cd src
python bot.py
```

### "Credentials not found"
Make sure `credentials/google_credentials.json` exists and is in the right location.

### "discord.errors.LoginFailure"
Your Discord bot token is incorrect. Double-check it in `.env`

### "Intents are not enabled"
Go to Discord Developer Portal > Your App > Bot > Enable "MESSAGE CONTENT INTENT"

### "No events created"
Check the console logs to see what Gemini returned. The message might not be clear enough.

### Gemini API quota exceeded
You get 1,500 requests/day free. Reset happens at midnight PT.

### Bot doesn't respond to DMs
Make sure "DIRECT MESSAGES" intent is enabled in Discord Developer Portal

---

## Security Notes

- Never commit `.env`, `token.pickle`, or `credentials/` to git (already in `.gitignore`)
- Never share your Discord bot token publicly
- If your token is leaked, regenerate it in Discord Developer Portal

---

## Customization

### Change timezone

Edit `src/services/calendar_service.py`:
```python
'timeZone': 'America/New_York',  # Change this
```

Common timezones:
- `America/New_York` (EST/EDT)
- `America/Chicago` (CST/CDT)
- `America/Los_Angeles` (PST/PDT)
- `America/Denver` (MST/MDT)
- `Europe/London` (GMT/BST)
- `Asia/Tokyo` (JST)

### Improve parsing

Edit the prompt in `src/services/gemini_parser.py` to handle specific formats better.

### Add notifications/reminders

Extend `create_calendar_event()` in `calendar_service.py`:
```python
event['reminders'] = {
    'useDefault': False,
    'overrides': [
        {'method': 'popup', 'minutes': 10},
        {'method': 'email', 'minutes': 60},
    ],
}
```

### Add new features

The bot is designed to be easily extended! See [FEATURES.md](FEATURES.md) for a complete guide.

**Quick example - adding a weather feature:**

1. Create `src/features/weather_feature.py`
2. Implement `get_capabilities()` to describe what it does
3. Implement `handle()` to process weather requests
4. Register in `discord_handler.py`

The AI will automatically learn to route weather-related messages to your new feature!

### Restrict bot to specific users

Edit `discord_handler.py` `on_message()`:
```python
# Only respond to specific user
ALLOWED_USER_ID = 123456789  # Your Discord user ID
if message.author.id != ALLOWED_USER_ID:
    return
```

### Adjust AI routing confidence

Edit `src/services/intent_router.py` to change how confident the AI needs to be:
```python
if feature_index is not None and confidence >= 0.6:  # Change 0.6 to higher/lower
```

Higher = more strict (only routes if very confident)
Lower = more lenient (routes even if somewhat uncertain)

---

## Next Steps

### Enhance the Calendar Feature
- Add support for recurring events
- Add ability to list upcoming events via Discord
- Add ability to delete/modify events
- Multiple calendar support
- Add event attendees/guests
- Natural language queries ("What's on my calendar tomorrow?")

### Add More Features
See [FEATURES.md](FEATURES.md) for ideas and examples:
- ⏰ **Reminders** - Set time-based reminders
- ✅ **Todo Lists** - Manage tasks
- 🌤️ **Weather** - Get weather forecasts
- 📧 **Email** - Send/read emails
- 📝 **Notes** - Save and retrieve notes
- 🌍 **Translation** - Translate text
- And literally anything else you can think of!

The AI routing makes adding new features incredibly easy.

---

## How This Works (Technical Overview)

**AI-Powered Intent Routing:**
1. User sends message to bot
2. Bot uses Gemini AI to analyze: "What is the user trying to do?"
3. AI compares message against all registered feature capabilities
4. AI selects best matching feature (with confidence score)
5. Bot routes to that feature
6. Feature processes the request
7. Bot sends response

**Why this is powerful:**
- No keyword matching required
- Users can phrase things naturally
- Adding new features is trivial - AI automatically learns to route to them
- Features describe their own capabilities
- Extensible to ANY task you can imagine

---

## Why Discord?

✅ Completely free (no limits on messages)
✅ Can run 24/7 on free hosting
✅ Works on phone, desktop, web
✅ Easy API and setup
✅ Can DM the bot directly
✅ Reliable and instant responses
✅ Works even when your laptop is closed

---

Enjoy your AI-powered assistant! 🎉

**For help adding features, see [FEATURES.md](FEATURES.md)**
