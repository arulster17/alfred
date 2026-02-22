"""
Shared test fixtures and setup.

Adds src/ to the path (since the bot runs from src/) and loads .env so
all tests have access to API keys without needing to start the Discord bot.
"""

import sys
import os

# Make src/ importable (mirrors running `cd src && python bot.py`)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_message():
    """Minimal stand-in for a Discord message object."""
    msg = MagicMock()
    msg.author.id = 99999
    msg.author.name = "test_user"
    msg.reply = AsyncMock()
    msg.channel.send = AsyncMock()
    return msg
