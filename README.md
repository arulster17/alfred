# alfred

A personal AI assistant via Discord DMs. Uses Google Gemini to understand natural language and route requests to modular feature handlers — no keyword matching, all AI-native.

## Features

- **Calendar** — Create, modify, and view Google Calendar events
- **YouTube Download** — Download YouTube videos as MP3 or MP4
- **Fun Facts** — Random interesting facts
- **Conversation** — General small talk and task guidance

## Tech Stack

- Python 3.14, discord.py, Google Gemini 2.5 Flash
- Google Calendar API (dual OAuth: readonly for all calendars, write for bot calendar only)
- yt-dlp + ffmpeg for YouTube downloads
- All APIs free tier

## Running Locally

```bash
pip install -r requirements.txt
cd src && python bot.py
```

See [SETUP.md](SETUP.md) for full setup instructions including API keys and OAuth configuration.

## Development

See [CLAUDE.md](CLAUDE.md) for architecture, conventions, and how to add new features.
