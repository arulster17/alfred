# Discord Assistant Bot

A modular Discord assistant bot powered by Google Gemini AI. Currently features automatic calendar event creation, with an architecture designed for easy expansion to additional capabilities.

## Overview

DM the bot on Discord with messages like "Meeting with John tomorrow at 3pm" and it automatically creates a Google Calendar event. The bot uses a modular feature system - calendar is just the first feature, and you can easily add more (reminders, todos, weather, etc.).

Built with Python, Discord.py, and Google Gemini - completely free and runs 24/7.

**Personal assistant via Discord DMs** - designed for private, one-on-one interaction.

## Features

- 🤖 Discord bot integration
- 🧩 Modular feature architecture - easy to extend
- 💬 Natural language parsing with Google Gemini 1.5 Flash
- 📅 Calendar: Automatic Google Calendar event creation
- 🆓 Completely free with generous quotas
- ⚡ Runs 24/7 on free hosting
- 📱 Works even when your laptop is closed

## Tech Stack

- **Python 3.11+** - Backend language
- **Discord.py** - Discord bot framework (FREE)
- **Google Gemini 1.5 Flash** - AI for message parsing (1,500 req/day FREE)
- **Google Calendar API** - Calendar integration (FREE)
- **Render/Railway** - Free 24/7 hosting

## Quick Start

1. Clone the repo and install dependencies
2. Set up Google Gemini API (free)
3. Set up Google Calendar API (free)
4. Create Discord bot (free)
5. Configure environment variables
6. Run locally or deploy to Render/Railway

**Full setup instructions:** See [SETUP.md](SETUP.md)

## Example Usage

Discord DM to bot:
```
Lunch with Sarah tomorrow at noon for 2 hours
```

Bot responds:
```
✓ Created event: Lunch with Sarah
📅 2026-02-17T12:00:00-08:00 → 2026-02-17T14:00:00-08:00
```

## Example Messages

- "Meeting tomorrow at 3pm"
- "Doctor appointment next Tuesday at 10am"
- "Lunch with Mike on Friday at noon for 1 hour"
- "Call with team next Monday at 2:30pm"
- "Dentist appointment on March 15th at 9am"

## Bot Commands

- `!help` - Show help message
- `!ping` - Check if bot is alive

## Cost Breakdown

- **Discord Bot:** FREE (unlimited messages)
- **Google Gemini API:** FREE (1,500 requests/day)
- **Google Calendar API:** FREE (generous quotas)
- **Hosting (Render/Railway):** FREE tier available
- **Total:** $0/month for personal use

## Project Structure

```
auto-calendar/
├── src/
│   ├── bot.py                       # Main bot entry point
│   ├── features/                    # Modular features
│   │   └── calendar_feature.py      # Calendar feature (add more here!)
│   ├── services/
│   │   ├── discord_handler.py       # Discord bot logic & routing
│   │   ├── gemini_parser.py         # Gemini AI parsing
│   │   └── calendar_service.py      # Google Calendar API
│   └── utils/
│       └── auth.py                  # Auth utilities
├── credentials/
│   └── google_credentials.json      # Google OAuth (gitignored)
├── .env                             # API keys (gitignored)
├── requirements.txt
├── SETUP.md                         # Detailed setup guide
├── FEATURES.md                      # Guide for adding new features
└── README.md
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
cd src
python bot.py
```

## Deployment

Deploy to Render or Railway for free 24/7 hosting. See [SETUP.md](SETUP.md) for detailed instructions.

## Limitations

- Gemini free tier: 1,500 requests/day (resets daily)
- Need to enable MESSAGE CONTENT INTENT in Discord Developer Portal

## Adding More Features

The bot is built with a modular architecture - see [FEATURES.md](FEATURES.md) for a guide on adding new features.

**Ideas for future features:**
- ⏰ Reminders - Set time-based reminders
- ✅ Todo Lists - Manage tasks and checklists
- 🌤️ Weather - Get weather forecasts
- 📰 News - Get news summaries
- 💱 Currency - Convert currencies
- 🌍 Translation - Translate text
- 📝 Notes - Save and retrieve notes
- 📊 Habit Tracker - Track daily habits

**Calendar feature enhancements:**
- [ ] Support for recurring events
- [ ] List upcoming events via Discord
- [ ] Delete/modify events via Discord
- [ ] Multiple calendar support
- [ ] Add event attendees
- [ ] Timezone detection
- [ ] Event reminders configuration
- [ ] Natural language queries ("What's on my calendar tomorrow?")

## Why Discord DMs?

✅ **Personal & Private** - Just you and the bot, no servers needed
✅ **Always Available** - Works on phone, desktop, web
✅ **24/7 Access** - Bot runs on free cloud hosting
✅ **Works Offline** - Your laptop can be closed/off
✅ **Completely Free** - No message limits
✅ **Instant Responses** - Real-time AI processing
✅ **Easy Access** - Open Discord, send DM, done

## License

MIT

## Contributing

Feel free to open issues or submit PRs!

---

Built with ❤️ using Google Gemini and completely free APIs
