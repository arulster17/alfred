# Alfred - AI Personal Assistant Bot (CLAUDE.md)

## Project Overview

Alfred is a personal AI assistant that operates via Discord DMs. It uses Google Gemini to understand natural language and route requests to modular feature handlers. Currently operational with four features: Calendar, Fun Facts, YouTube Download, and Conversation.

**Run the bot:**
```bash
cd src && python bot.py
```

---

## Architecture

```
Discord DM → discord_handler.py → intent_router.py (Gemini) → Feature Handler → Response
```

- **100% AI-native**: Zero keyword matching anywhere. All routing and parsing is done via Gemini.
- **Modular features**: Each feature in `src/features/` is an independent drop-in module.
- **Conversation as fallback**: Registered LAST so task features get routing priority.
- **Context system**: Per-user, last 10 messages / 15 minutes (in-memory, resets on restart).

---

## Critical Rules

### NEVER add keyword matching. This is the #1 architectural rule.
These patterns are forbidden:
```python
keywords = ["remind", "calendar", ...]          # No keyword lists
if "word" in message_text.lower(): ...          # No string contains checks
any(kw in text for kw in keywords)              # No keyword iteration
re.search(r'pattern', text)                     # No regex fallbacks for routing/parsing
def can_handle(self, text): return ...          # No can_handle methods
```
All intent detection and data extraction goes through Gemini AI.

### Always use `gemini-2.5-flash` (not 2.0, not 1.5)

### Register task features BEFORE the conversation feature in `_load_features()`

### Update `PROJECT_SUMMARY.md` after significant changes

---

## Key Files

| File | Purpose |
|------|---------|
| `src/bot.py` | Entry point |
| `src/config/bot_context.py` | Alfred's personality (single source of truth) |
| `src/services/discord_handler.py` | Discord bot + feature registration + context management |
| `src/services/intent_router.py` | AI-powered feature routing (Gemini, confidence threshold: 0.6) |
| `src/services/gemini_parser.py` | Natural language → calendar event data |
| `src/services/calendar_service.py` | Google Calendar API (create/search/modify events) |
| `src/features/calendar_feature.py` | Calendar: create, modify, view events |
| `src/features/fun_fact_feature.py` | Fun fact generation |
| `src/features/youtube_feature.py` | YouTube MP3/MP4 download (yt-dlp + ffmpeg) |
| `src/features/conversation_feature.py` | Small talk fallback |
| `src/utils/auth.py` | Auth utilities (minimal) |

**Credentials (git-ignored):**
- `credentials/user_credentials.json` → OAuth readonly scope (reads ALL calendars)
- `credentials/bot_credentials.json` → OAuth full scope (writes to bot calendar only)
- `user_token.pickle` / `bot_token.pickle` → OAuth tokens

---

## Adding a New Feature

1. Create `src/features/feature_name.py`:
```python
class MyFeature:
    def __init__(self):
        self.name = "My Feature"
        self.description = "What it does"

    def get_capabilities(self) -> str:
        return """
        Detailed description of what this feature handles.
        Include many examples so the AI router can match accurately.
        """

    async def handle(self, message, message_text, context=None) -> str:
        # Use Gemini to parse intent and extract data
        # Return a string response
        pass
```

2. Register in `src/services/discord_handler.py` in `_load_features()` **before** the conversation feature.

3. The AI router automatically learns to route to it based on `get_capabilities()`.

**No `can_handle()` method. No keywords. AI only.**

---

## Tech Stack

- **Python 3.14**
- **discord.py >=2.6.4**
- **google-genai >=0.3.0** (the new SDK — NOT `google-generativeai`)
- **google-auth / google-auth-oauthlib / google-api-python-client** — Calendar API
- **python-dotenv >=1.0.1**
- **yt-dlp >=2026.2.4** + **ffmpeg** (system dependency) — YouTube downloads
- **AI model**: `gemini-2.5-flash` for all routing and parsing

---

## Environment Variables (`.env`)

```bash
DISCORD_BOT_TOKEN=...
DISCORD_OWNER_ID=...          # Optional: bot sends "Ready!" DM on startup
GOOGLE_GEMINI_API_KEY=...
GOOGLE_CALENDAR_ID=...        # The bot's write calendar ID (not "primary")
```

Never commit `.env`, `credentials/`, or `*.pickle` files.

---

## User & Project Preferences

- **User timezone**: `America/Los_Angeles` (PST/PDT)
- **DM-first design**: Personal assistant via DMs, not a server bot
- **Personality**: Professional, concise, task-focused. Brief small talk (1-2 exchanges) then redirects.
- **All APIs free**: Never suggest paid tiers or paid APIs
- **Preferred hosting**: Fly.io (free, always-on, no spin-down)
- **Simple code**: Avoid over-engineering; don't add features not explicitly requested
- **Working code > documentation**

---

## What NOT to Do

- Add keyword matching in any form
- Use `gemini-2.0-flash` or `gemini-1.5-flash` — it's `gemini-2.5-flash`
- Make Alfred overly chatty
- Suggest server-based (non-DM) features
- Suggest re-doing the API/OAuth setup (already complete)
- Over-engineer simple requests
- Skip updating `PROJECT_SUMMARY.md` after significant changes

---

## Current Features Status

- **Calendar**: Create, modify, view events — fully tested
- **Fun Facts**: Working
- **YouTube Download**: Implemented (MP3/MP4, up to 5 URLs, 25MB Discord limit) — needs testing
- **Conversation**: Working (fallback/small talk)
- **AI Routing**: Working (0.6 confidence threshold)
- **Dual OAuth**: Working (readonly for view, write for bot calendar)
- **Context system**: Working (10 messages / 15 min per user, in-memory)

---

## Common Debugging

- **Wrong feature routing**: Improve that feature's `get_capabilities()` description
- **Calendar parsing errors**: Check `gemini_parser.py` prompt; look at Gemini response in logs
- **Alfred too chatty/rigid**: Adjust `bot_context.py`
- **Run from `src/` directory**: Imports assume `src/` as working directory

Console logs show: `👤 USER`, `📚 context`, `🤖 routing decision`, `🤵 ALFRED response`

---

## Deployment

**Low priority.** Bot runs locally for now. Cloud hosting is a future consideration — no platform decided yet. Key constraint when the time comes: OAuth tokens (`*.pickle`) can't be regenerated headlessly.
