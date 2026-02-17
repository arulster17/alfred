"""
Authentication utilities for Google Calendar.

This module provides helper functions for OAuth2 authentication.
Currently, the main authentication logic is in calendar_service.py
but this can be extended for additional auth-related utilities.
"""

def get_timezone():
    """
    Get the user's timezone.
    For now returns a default, but can be extended to detect or configure timezone.
    """
    return 'America/Los_Angeles'
