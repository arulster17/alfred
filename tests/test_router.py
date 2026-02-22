"""
Tests for the AI intent router.

Verifies that the router correctly assigns messages to the right feature.
These tests call real Gemini — they test routing logic, not mocked responses.
"""

import pytest
from services.intent_router import IntentRouter
from features.calendar_feature import CalendarFeature
from features.fun_fact_feature import FunFactFeature
from features.youtube_feature import YouTubeFeature
from features.search_feature import SearchFeature
from features.conversation_feature import ConversationFeature


@pytest.fixture
def router():
    r = IntentRouter()
    r.register_feature(CalendarFeature())
    r.register_feature(FunFactFeature())
    r.register_feature(YouTubeFeature())
    r.register_feature(SearchFeature())
    r.register_feature(ConversationFeature())
    return r


@pytest.mark.parametrize("message,expected", [
    # Calendar - create
    ("schedule a meeting tomorrow at 3pm", "Calendar"),
    ("add lunch with Sarah on Friday at noon", "Calendar"),
    # Calendar - view
    ("what's on my calendar today?", "Calendar"),
    ("what do I have this week?", "Calendar"),
    # Search - factual
    ("why do Muslims fast during Ramadan?", "Search"),
    ("how does a compiler work?", "Search"),
    ("what's the travel time from San Diego to Los Angeles?", "Search"),
    # Fun fact
    ("tell me a fun fact", "FunFact"),
    ("give me an interesting fact", "FunFact"),
    # YouTube
    ("download this as mp3: https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube Downloader"),
    # Conversation
    ("hey alfred how are you", "Conversation"),
    ("thanks!", "Conversation"),
])
def test_routing(router, message, expected):
    result = router.route(message)
    assert result is not None, f"Router returned None for: {message!r}"
    assert result.name == expected, f"Expected {expected!r}, got {result.name!r} for: {message!r}"
