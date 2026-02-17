import os
from dotenv import load_dotenv
from services.discord_handler import AssistantBot, setup_bot_commands

# Load environment variables
load_dotenv()

def main():
    """
    Main entry point for the Discord assistant bot.
    Initializes and runs the bot with all available features.
    """

    # Get Discord token from environment
    token = os.getenv('DISCORD_BOT_TOKEN')

    if not token:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables")
        print("Please set it in your .env file")
        return

    # Create bot instance
    bot = AssistantBot()

    # Set up custom commands
    setup_bot_commands(bot)

    # Run the bot
    print("Starting Discord assistant bot...")
    bot.run(token)

if __name__ == '__main__':
    main()
