"""
Conversation Feature - Handles greetings, small talk, and general queries.

This feature handles non-task messages while staying true to Alfred's
task-oriented personality.
"""

import os
from google import genai
from config.bot_context import BOT_NAME, get_system_context

# Lazy-load client
_client = None

def _get_client():
    """Get or create the Gemini client"""
    global _client
    if _client is None:
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "GOOGLE_GEMINI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        _client = genai.Client(api_key=api_key)
    return _client

class ConversationFeature:
    """
    Handles conversational messages and small talk.
    """

    def __init__(self):
        self.name = "Conversation"
        self.description = "Handle greetings, small talk, and general questions"

    def get_capabilities(self):
        """
        Tell the AI router what this feature can do.
        """
        return f"""
This feature handles conversational, non-task messages.

Examples of what this feature handles:
- "Hello", "Hi", "Hey Alfred"
- "How are you?", "What's up?"
- "What can you do?", "Help me"
- "Thanks!", "Thank you"
- General questions about the bot
- Small talk that doesn't involve tasks
- Questions about capabilities

This is a FALLBACK feature - use it when the message doesn't match any specific task feature
        """.strip()


    async def handle(self, message, message_text, context=None):
        """
        Process conversational messages with Alfred's personality.

        Args:
            message: Discord message object
            message_text (str): The user's message text
            context (list): Optional conversation context [(timestamp, role, message), ...]

        Returns:
            str: Response to send back to the user
        """
        try:
            client = _get_client()

            # Format context if available
            context_str = ""
            if context:
                context_str = "\nRecent conversation:\n"
                for timestamp, role, msg in context:
                    role_label = "User" if role == "user" else "Alfred"
                    context_str += f"{role_label}: {msg}\n"
                context_str += "\n"

            # Build prompt with bot context
            system_context = get_system_context()
            prompt = f"""
{system_context}
{context_str}
User message: "{message_text}"

You are Alfred responding to the user. Keep your response:
- Under 2-3 sentences
- Friendly but concise
- Task-oriented (gently guide toward how you can help)
- Natural and conversational
- Use the conversation context above to provide relevant responses
- DO NOT address the user as "Alfred" - YOU are Alfred, THEY are the user

If the user is just greeting you or making small talk, respond warmly but briefly offer to help with tasks.
If they're asking what you can do, explain your calendar capabilities.
If they're asking deep/philosophical questions, politely redirect to your actual purpose.

Return ONLY your response text, no extra formatting or labels.
            """.strip()

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )

            return response.text.strip()

        except Exception as e:
            print(f"Error in conversation feature: {str(e)}")
            import traceback
            traceback.print_exc()
            # Simple fallback when AI fails
            return f"Hello! I'm {BOT_NAME}, your assistant. I can help with calendar events and more. What would you like to do?"
