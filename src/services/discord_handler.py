import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
from features.calendar_feature import CalendarFeature
from features.conversation_feature import ConversationFeature
from features.fun_fact_feature import FunFactFeature
from features.youtube_feature import YouTubeFeature
from features.search_feature import SearchFeature
from services.intent_router import IntentRouter
from config.bot_context import BOT_NAME, get_bot_intro

class AssistantBot(commands.Bot):
    """
    AI-Powered Discord assistant bot.

    Uses Google Gemini to intelligently understand user intent and route
    messages to the appropriate feature handler.

    Currently supports:
    - Calendar: Create Google Calendar events from natural language
    - Conversation context: Remembers last 10 messages from last 15 minutes

    Future features can be added to the features/ directory.
    The AI will automatically learn to route to them.
    """

    def __init__(self):
        # Set up intents (permissions for the bot)
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read message content
        intents.dm_messages = True      # Allow DMs

        # Disable default help command so we can add our own
        super().__init__(command_prefix='!', intents=intents, help_command=None)

        # Initialize AI-powered intent router
        self.router = IntentRouter()

        # Conversation context tracking (per user)
        # Structure: {user_id: [(timestamp, role, message), ...]}
        self.conversation_history = defaultdict(list)

        # Context settings
        self.MAX_CONTEXT_MESSAGES = 10  # Keep last N messages
        self.CONTEXT_WINDOW_MINUTES = 15  # Only keep messages from last N minutes

        # Load features
        self._load_features()

    def _load_features(self):
        """Load all available features and register them with the AI router"""
        # Task-oriented features (higher priority)
        calendar = CalendarFeature()
        self.router.register_feature(calendar)

        fun_fact = FunFactFeature()
        self.router.register_feature(fun_fact)

        youtube = YouTubeFeature()
        self.router.register_feature(youtube)

        search = SearchFeature()
        self.router.register_feature(search)

        # Conversation feature (fallback for non-task messages)
        conversation = ConversationFeature()
        self.router.register_feature(conversation)

        # Future task features can be added here:
        # reminder = ReminderFeature()
        # self.router.register_feature(reminder)
        #
        # todo = TodoFeature()
        # self.router.register_feature(todo)
        #
        # weather = WeatherFeature()
        # self.router.register_feature(weather)

        print(f"Loaded {len(self.router.features)} features:")
        for feature in self.router.features:
            print(f"  - {feature.name}: {feature.description}")

    def _add_to_context(self, user_id, role, message_text):
        """
        Add a message to the conversation context.

        Args:
            user_id: Discord user ID
            role: 'user' or 'assistant'
            message_text: The message content
        """
        timestamp = datetime.now()
        self.conversation_history[user_id].append((timestamp, role, message_text))

    def _get_context(self, user_id):
        """
        Get recent conversation context for a user.

        Applies hybrid filtering:
        - Only messages from last CONTEXT_WINDOW_MINUTES
        - Only last MAX_CONTEXT_MESSAGES messages

        Args:
            user_id: Discord user ID

        Returns:
            list: List of (timestamp, role, message) tuples
        """
        if user_id not in self.conversation_history:
            return []

        now = datetime.now()
        cutoff_time = now - timedelta(minutes=self.CONTEXT_WINDOW_MINUTES)

        # Filter by time window
        recent_messages = [
            msg for msg in self.conversation_history[user_id]
            if msg[0] > cutoff_time
        ]

        # Keep only last N messages
        recent_messages = recent_messages[-self.MAX_CONTEXT_MESSAGES:]

        # Update the stored history to remove old messages
        self.conversation_history[user_id] = recent_messages

        return recent_messages

    def _format_context_for_prompt(self, context):
        """
        Format conversation context for inclusion in AI prompts.

        Args:
            context: List of (timestamp, role, message) tuples

        Returns:
            str: Formatted context string
        """
        if not context:
            return ""

        formatted = "Recent conversation:\n"
        for timestamp, role, message in context:
            role_label = "User" if role == "user" else "Alfred"
            formatted += f"{role_label}: {message}\n"

        return formatted

    async def on_ready(self):
        """Called when bot successfully connects to Discord"""
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is ready to receive messages')

        # Send startup message to configured user
        import os
        owner_id = os.getenv('DISCORD_OWNER_ID')
        if owner_id:
            try:
                owner_id = int(owner_id)
                user = await self.fetch_user(owner_id)
                await user.send("✅ Ready to go!")
                print(f"Sent startup message to {user.name}")
            except Exception as e:
                print(f"Could not send startup message: {e}")

    async def on_message(self, message):
        """Called whenever a message is sent that the bot can see"""

        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Process commands first (like !help)
        await self.process_commands(message)

        # Only process DMs or messages that mention the bot
        if not isinstance(message.channel, discord.DMChannel) and self.user not in message.mentions:
            return

        # Get the message text (remove bot mention if present)
        message_text = message.content.replace(f'<@{self.user.id}>', '').strip()

        # Ignore empty messages or command messages
        if not message_text or message_text.startswith('!'):
            return

        # Show typing indicator while processing
        async with message.channel.typing():
            # Route message to appropriate feature
            await self._route_message(message, message_text)

    async def _route_message(self, message, message_text):
        """
        Use AI to route the message to the appropriate feature.

        The AI router analyzes the user's intent and selects the best feature
        to handle the request.
        """
        try:
            user_id = message.author.id

            # Get recent conversation context
            context = self._get_context(user_id)

            # Log user input
            print(f"\n{'='*60}")
            print(f"👤 USER ({message.author.name}): {message_text}")
            if context:
                print(f"📚 Context: {len(context)} message(s) in memory")
            print(f"{'='*60}")

            # Add user message to context
            self._add_to_context(user_id, "user", message_text)

            # Use AI to determine which feature should handle this
            handler = self.router.route(message_text, context=context)

            if handler:
                print(f"🤖 AI Router selected: {handler.name}")

                try:
                    # Pass context to the handler
                    response = await handler.handle(message, message_text, context=context)

                    # Add Alfred's response to context
                    self._add_to_context(user_id, "assistant", response)

                    # Log Alfred's response
                    print(f"\n🤵 ALFRED: {response}")
                    print(f"{'='*60}\n")

                    await message.reply(response)

                except Exception as e:
                    error_str = str(e)
                    # Check if it's a rate limit error
                    if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                        response = (
                            "⚠️ I'm currently experiencing API rate limit issues with Google Gemini.\n\n"
                            "**What's happening:** The Gemini API quota has been exceeded.\n\n"
                            "**What you can do:**\n"
                            "• Wait a few minutes and try again\n"
                            "• Check API usage at: https://ai.dev/rate-limit\n"
                            "• The quota may reset at midnight PT\n\n"
                            "Sorry for the inconvenience! This is a temporary issue with the free tier API limits."
                        )
                    else:
                        response = f"An error occurred while processing your request: {str(e)}"

                    print(f"\n🤵 ALFRED: {response}")
                    print(f"{'='*60}\n")

                    await message.reply(response)

            else:
                # No feature matched - provide helpful message
                available_features = self.router.get_feature_summary()
                response = (
                    "I'm not sure how to help with that yet.\n\n"
                    f"Here's what I can do:\n{available_features}\n\n"
                    "Type `!help` for more information and examples."
                )

                # Add to context
                self._add_to_context(user_id, "assistant", response)

                # Log Alfred's response
                print(f"\n🤵 ALFRED: {response}")
                print(f"{'='*60}\n")

                await message.reply(response)

        except Exception as e:
            error_str = str(e)
            print(f"❌ Error routing message: {error_str}")

            # Check if it's a rate limit error
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                error_response = (
                    "⚠️ I'm currently experiencing API rate limit issues with Google Gemini.\n\n"
                    "**What's happening:** The Gemini API quota has been exceeded.\n\n"
                    "**What you can do:**\n"
                    "• Wait a few minutes and try again\n"
                    "• Check API usage at: https://ai.dev/rate-limit\n"
                    "• The quota may reset at midnight PT\n\n"
                    "Sorry for the inconvenience! This is a temporary issue with the free tier API limits."
                )
            else:
                error_response = f"An error occurred: {str(e)}"

            # Log error response
            print(f"\n🤵 ALFRED: {error_response}")
            print(f"{'='*60}\n")

            await message.reply(error_response)


def setup_bot_commands(bot):
    """Add custom commands to the bot"""

    @bot.command(name='help')
    async def help_command(ctx):
        """Show help message"""

        # Build help text dynamically from features
        features_help = bot.router.get_feature_summary()

        help_text = f"""
**Hello! I'm {BOT_NAME}, your AI assistant.**

I understand natural language, so just tell me what you need!

**What I can do:**
📅 **Calendar** - Create and manage events
💬 **Chat** - Answer questions and have brief conversations

**Example requests:**
• "Meeting tomorrow at 3pm"
• "Add lunch with Sarah on Friday at noon"
• "I have a call on Wednesday from 1-2 about the project"

**Commands:**
• `!help` - Show this message
• `!ping` - Check if I'm responsive
• `!features` - List all capabilities

💬 **Tip:** You can chat naturally with me! I'm friendly but focused on helping you stay organized.
        """
        await ctx.send(help_text)

    @bot.command(name='ping')
    async def ping_command(ctx):
        """Check if bot is responsive"""
        await ctx.send(f'Pong! 🏓 Latency: {round(bot.latency * 1000)}ms')

    @bot.command(name='features')
    async def features_command(ctx):
        """List all available features"""
        features_list = bot.router.get_feature_summary()
        await ctx.send(f"**Available Features:**\n{features_list}")
