"""
AI-Powered Intent Router

Uses Google Gemini to intelligently route user messages to the appropriate feature.
Instead of keyword matching, the AI understands what the user wants to do and
routes to the correct feature handler.
"""

import os
import json
from google import genai

# Lazy-load client to ensure env vars are loaded first
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

class IntentRouter:
    """
    Routes user messages to features using AI-powered intent detection.
    """

    def __init__(self):
        self.features = []

    def register_feature(self, feature):
        """
        Register a feature with the router.

        Args:
            feature: Feature instance with name, description, and capabilities
        """
        self.features.append(feature)

    def route(self, message_text, context=None):
        """
        Use AI to determine which feature should handle this message.

        Args:
            message_text (str): The user's message
            context (list): Optional conversation context [(timestamp, role, message), ...]

        Returns:
            Feature instance or None if no suitable feature found
        """
        if not self.features:
            return None

        # Build feature descriptions for the AI
        feature_descriptions = []
        for i, feature in enumerate(self.features):
            feature_descriptions.append({
                "index": i,
                "name": feature.name,
                "description": feature.description,
                "capabilities": feature.get_capabilities()
            })

        # Create prompt for Gemini
        prompt = self._build_routing_prompt(message_text, feature_descriptions, context=context)

        try:
            # Ask Gemini which feature should handle this
            client = _get_client()
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            response_text = response.text.strip()

            # Clean up response (remove markdown if present)
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # Parse JSON response
            result = json.loads(response_text)

            feature_index = result.get('feature_index')
            confidence = result.get('confidence', 0)

            # Return feature if confidence is high enough
            if feature_index is not None and confidence >= 0.6:
                return self.features[feature_index]

            # If no clear match, return None
            return None

        except Exception as e:
            error_str = str(e)
            print(f"Error in intent routing: {error_str}")

            # Check if it's a rate limit error
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                # Return None to trigger special rate limit message
                return None

            # Fallback: try first feature that says it can handle
            for feature in self.features:
                if hasattr(feature, 'can_handle') and feature.can_handle(message_text):
                    return feature
            return None

    def _build_routing_prompt(self, message_text, feature_descriptions, context=None):
        """
        Build the prompt for Gemini to route the message.

        Args:
            message_text (str): User's message
            feature_descriptions (list): List of feature metadata
            context (list): Optional conversation context

        Returns:
            str: Prompt for Gemini
        """
        features_json = json.dumps(feature_descriptions, indent=2)

        # Format context if available
        context_str = ""
        if context:
            context_str = "\nRecent conversation:\n"
            for timestamp, role, msg in context:
                role_label = "User" if role == "user" else "Alfred"
                context_str += f"{role_label}: {msg}\n"
            context_str += "\n"

        prompt = f"""
You are an intelligent routing system for a personal assistant bot.
{context_str}
User message: "{message_text}"

Available features:
{features_json}

Your task: Determine which feature should handle this user's message.

Rules:
1. Analyze what the user is trying to accomplish
2. Consider the conversation context above (if any) to understand references like "it", "that", "the event"
3. Match their intent to the most appropriate feature
4. Consider the capabilities and examples of each feature
5. If the message doesn't clearly match any feature, return feature_index: null
6. Be generous with calendar - if someone mentions time/date/event, it's probably calendar

Return ONLY valid JSON with this structure:
{{
  "feature_index": <index of best matching feature, or null>,
  "confidence": <confidence level 0.0-1.0>,
  "reasoning": "<brief explanation of why this feature matches>"
}}

Examples:
- "Meeting tomorrow at 3pm" → calendar feature (high confidence)
- After creating event, user says "make it 2 hours" → calendar feature (using context)
- "Remind me to call mom" → reminder feature if available, else null
- "What's the weather?" → weather feature if available, else null
- "Random chat message" → conversation feature (low confidence)
"""
        return prompt

    def get_feature_summary(self):
        """
        Get a summary of all registered features for display.

        Returns:
            str: Human-readable list of features
        """
        if not self.features:
            return "No features available"

        summary = []
        for feature in self.features:
            summary.append(f"• **{feature.name}**: {feature.description}")

        return "\n".join(summary)
