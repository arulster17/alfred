"""
Tests for individual feature handlers.

These call real Gemini and (for Calendar) the real Google Calendar API.
YouTube is excluded — its handle() downloads files and sends them via Discord,
which doesn't make sense outside of a real bot session.
"""

import pytest
from features.calendar_feature import CalendarFeature
from features.search_feature import SearchFeature
from features.conversation_feature import ConversationFeature
from features.fun_fact_feature import FunFactFeature


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

class TestCalendar:
    @pytest.mark.asyncio
    async def test_view_today(self, mock_message):
        feature = CalendarFeature()
        response = await feature.handle(mock_message, "what's on my calendar today?")
        assert isinstance(response, str)
        assert len(response) > 5

    @pytest.mark.asyncio
    async def test_view_specific_day(self, mock_message):
        feature = CalendarFeature()
        response = await feature.handle(mock_message, "what do I have next Monday?")
        assert isinstance(response, str)
        assert len(response) > 5

    @pytest.mark.asyncio
    async def test_bad_request_doesnt_crash(self, mock_message):
        feature = CalendarFeature()
        response = await feature.handle(mock_message, "asdfghjkl calendar???")
        assert isinstance(response, str)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class TestSearch:
    @pytest.mark.asyncio
    async def test_factual_question(self, mock_message):
        feature = SearchFeature()
        response = await feature.handle(mock_message, "why do Muslims fast during Ramadan?")
        assert isinstance(response, str)
        assert len(response) > 20

    @pytest.mark.asyncio
    async def test_travel_time(self, mock_message):
        feature = SearchFeature()
        response = await feature.handle(mock_message, "travel time from San Diego to Los Angeles by car")
        assert isinstance(response, str)
        assert len(response) > 20

    @pytest.mark.asyncio
    async def test_how_to_question(self, mock_message):
        feature = SearchFeature()
        response = await feature.handle(mock_message, "how do I fix a merge conflict in git?")
        assert isinstance(response, str)
        assert len(response) > 20


# ---------------------------------------------------------------------------
# Fun Fact
# ---------------------------------------------------------------------------

class TestFunFact:
    @pytest.mark.asyncio
    async def test_returns_a_fact(self, mock_message):
        feature = FunFactFeature()
        response = await feature.handle(mock_message, "tell me a fun fact")
        assert isinstance(response, str)
        assert len(response) > 20

    @pytest.mark.asyncio
    async def test_topical_fact(self, mock_message):
        feature = FunFactFeature()
        response = await feature.handle(mock_message, "give me a fun fact about space")
        assert isinstance(response, str)
        assert len(response) > 20


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

class TestConversation:
    @pytest.mark.asyncio
    async def test_greeting(self, mock_message):
        feature = ConversationFeature()
        response = await feature.handle(mock_message, "hey alfred, how are you?")
        assert isinstance(response, str)
        assert len(response) > 5

    @pytest.mark.asyncio
    async def test_thanks(self, mock_message):
        feature = ConversationFeature()
        response = await feature.handle(mock_message, "thanks!")
        assert isinstance(response, str)
        assert len(response) > 5
