"""
Fun Fact Feature - Provides interesting random facts to the user.

A simple entertainment feature for the assistant bot.
"""

import os
from google import genai

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

class FunFactFeature:
    """
    Handles fun fact requests.
    """

    def __init__(self):
        self.name = "FunFact"
        self.description = "Provide interesting random facts"

    def get_capabilities(self):
        """
        Describe what this feature can do for the AI router.

        Returns:
            str: Detailed description of capabilities
        """
        return """
This feature can:
- Provide interesting random facts
- Share trivia and knowledge
- Entertain with fun information

Examples of what this feature handles:
- "Tell me a fun fact"
- "Give me an interesting fact"
- "Share a random fact"
- "Tell me something interesting"
- "Got any fun facts?"

        """.strip()


    async def handle(self, message, message_text, context=None):
        """
        Generate a fun fact.

        Args:
            message: Discord message object
            message_text (str): The user's message text
            context (list): Optional conversation context

        Returns:
            str: A fun fact
        """
        try:
            client = _get_client()

            # Format conversation context if available
            context_str = ""
            if context:
                context_str = "\nRecent conversation:\n"
                for timestamp, role, msg in context:
                    role_label = "User" if role == "user" else "Alfred"
                    context_str += f"{role_label}: {msg}\n"
                context_str += "\n"

            prompt = f"""
{context_str}You are Alfred, a knowledgeable assistant. Provide a single interesting fun fact.

Requirements:
- Keep it brief (2-3 sentences max)
- Make it genuinely interesting
- Ensure it's accurate
- Use a friendly, engaging tone
- Don't start with "Here's a fun fact" or similar - just state the fact
- If the conversation context suggests a topic, you can provide a related fact

Return ONLY the fun fact text.
            """.strip()

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )

            return response.text.strip()

        except Exception as e:
            print(f"Error in fun fact feature: {str(e)}")
            return "Sorry, I couldn't retrieve a fun fact right now. Please try again!"
