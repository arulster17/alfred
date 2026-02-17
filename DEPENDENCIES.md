# Dependencies Documentation

**Last Updated:** 2026-02-17

## Core Dependencies

### Discord Integration
- **discord.py >=2.6.4**
  - Purpose: Discord bot framework
  - Why: Handles all Discord API interactions, message events, DM support
  - License: MIT
  - Docs: https://discordpy.readthedocs.io/

### Google Gemini AI
- **google-genai >=0.3.0**
  - Purpose: Google Gemini AI SDK (new unified SDK)
  - Why: Powers AI routing and natural language parsing
  - Model used: `gemini-2.0-flash`
  - License: Apache 2.0
  - Docs: https://ai.google.dev/gemini-api/docs
  - Note: Replaces deprecated `google-generativeai` package

### Google Calendar Integration
- **google-auth >=2.37.0**
  - Purpose: Google authentication base library
  - Why: Core authentication for Google services

- **google-auth-oauthlib >=1.2.1**
  - Purpose: OAuth2 authentication flow
  - Why: Handles browser-based Google Calendar authorization

- **google-auth-httplib2 >=0.2.0**
  - Purpose: HTTP transport for Google Auth
  - Why: Required by google-api-python-client

- **google-api-python-client >=2.155.0**
  - Purpose: Google Calendar API client
  - Why: Creates, modifies, searches calendar events
  - Docs: https://developers.google.com/calendar/api/v3/reference

### Supporting Libraries
- **python-dotenv >=1.0.1**
  - Purpose: Environment variable management
  - Why: Loads API keys and config from .env file
  - License: BSD

- **protobuf >=5.29.2,<6.0.0**
  - Purpose: Protocol buffers serialization
  - Why: Required by google-genai for API communication
  - Note: Version constrained to <6.0.0 for compatibility

- **grpcio >=1.68.1**
  - Purpose: gRPC framework
  - Why: Used by google-genai for efficient API calls

- **grpcio-status >=1.68.1**
  - Purpose: gRPC status codes
  - Why: Proper error handling for gRPC calls

## Python Version

- **Python 3.14.0**
  - All dependencies are tested and compatible with Python 3.14
  - Specified in `runtime.txt` for deployment

## Installation

```bash
pip install -r requirements.txt
```

## API Keys Required

All keys are configured in `.env` file (see `.env.example`):

1. **DISCORD_BOT_TOKEN**
   - Get from: https://discord.com/developers/applications
   - Free tier: Unlimited messages
   - Purpose: Bot authentication

2. **GOOGLE_GEMINI_API_KEY**
   - Get from: https://makersuite.google.com/app/apikey
   - Free tier: Varies by model (check https://ai.google.dev/pricing)
   - Currently using: gemini-2.0-flash
   - Purpose: AI routing and natural language parsing

3. **GOOGLE_CALENDAR_ID**
   - Default: "primary" (main calendar)
   - Alternative: Specific calendar ID for testing
   - Format: `abc123@group.calendar.google.com`
   - Purpose: Which calendar to create events in

## OAuth Credentials

- **Google Calendar OAuth**
  - File: `credentials/google_credentials.json`
  - Get from: Google Cloud Console → APIs & Services → Credentials
  - Type: OAuth 2.0 Client ID (Desktop app)
  - Scope: `https://www.googleapis.com/auth/calendar`
  - Token storage: `token.pickle` (auto-generated on first auth)

## Dependency Update Strategy

### When to Update
- Monthly: Check for security updates
- As needed: When features require newer versions
- Carefully: Test thoroughly before updating major versions

### How to Update
```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements.txt
pip freeze > requirements.txt
```

### Version Constraints
- Use `>=` for most packages (allows minor updates)
- Use `<` for protobuf (compatibility constraint)
- Pin exact versions if stability issues occur

## Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'google.genai'**
- Solution: Ensure you installed `google-genai` not `google-generativeai`
- Run: `pip install google-genai>=0.3.0`

**Gemini API quota exceeded**
- Check usage: https://ai.dev/rate-limit
- Free tier varies by model
- Consider switching models or upgrading plan

**Discord.py compatibility issues**
- Ensure Python 3.14 compatible version
- Check: `pip show discord.py`

**Google Calendar auth fails**
- Delete `token.pickle` and re-authenticate
- Ensure OAuth credentials are for "Desktop app"
- Check scopes include `https://www.googleapis.com/auth/calendar`

## License Information

This project uses the following licenses:
- discord.py: MIT
- google-genai: Apache 2.0
- google-api-python-client: Apache 2.0
- python-dotenv: BSD

See individual package documentation for full license texts.
