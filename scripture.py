"""scripture.py — Daily verse selection and Telegram delivery.

Selects a verse from data/verses.json based on theme rotation,
delivers it via Telegram, and tracks sent verses to avoid repeats.

Themes: faith, hope, love, strength, peace, wisdom

Usage:
    python scripture.py          # Send today's verse
    python scripture.py --theme faith  # Send a verse from a specific theme

Cron: 0 6 * * * (6:00 AM daily)
"""

import json
import os
import random
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
VERSES_FILE = DATA_DIR / "verses.json"
SENT_LOG = DATA_DIR / ".sent_verses.json"

THEMES = ["faith", "hope", "love", "strength", "peace", "wisdom"]


def load_verses():
    """Load all verses from verses.json.

    Returns:
        list[dict]: List of verse objects with keys:
            - reference (str): e.g. "John 3:16"
            - text (str): The verse text
            - theme (str): One of THEMES
    """
    pass


def get_sent_verses():
    """Load the log of previously sent verse references.

    Returns:
        list[str]: List of verse references already sent.
    """
    pass


def mark_verse_sent(reference):
    """Record a verse reference as sent.

    Args:
        reference (str): The verse reference, e.g. "John 3:16"
    """
    pass


def select_verse(theme=None):
    """Select a verse that hasn't been sent yet.

    Uses theme rotation based on the day of the year if no theme
    is specified. Resets the sent log when all verses have been used.

    Args:
        theme (str, optional): Specific theme to select from.

    Returns:
        dict: The selected verse object.
    """
    pass


def format_message(verse):
    """Format a verse into a Telegram-friendly message.

    Args:
        verse (dict): Verse object with reference, text, and theme.

    Returns:
        str: Formatted message string with emoji and attribution.
    """
    pass


def send_to_telegram(message):
    """Send a message to the configured Telegram chat.

    Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment.

    Args:
        message (str): The message text to send.

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    pass


def main():
    """Entry point: select today's verse and send it."""
    pass


if __name__ == "__main__":
    main()
