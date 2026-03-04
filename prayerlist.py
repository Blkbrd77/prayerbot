"""prayerlist.py — Prayer list CRUD and weekly review.

Manages a prayer list stored in data/prayers.json with operations
to add, remove, list, and review prayer requests. Sends a weekly
Sunday summary via Telegram.

Usage:
    python prayerlist.py --add "Prayer request text" [--category healing]
    python prayerlist.py --remove <id>
    python prayerlist.py --answered <id>
    python prayerlist.py --list
    python prayerlist.py --review

Cron (Sunday review): 0 7 * * 0 (7:00 AM Sundays)
"""

import json
import uuid
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PRAYERS_FILE = DATA_DIR / "prayers.json"

CATEGORIES = ["healing", "guidance", "gratitude", "family",
              "provision", "world", "personal", "other"]


def load_prayers():
    """Load the prayer list from prayers.json.

    Returns:
        list[dict]: List of prayer objects with keys:
            - id (str): UUID
            - text (str): The prayer request
            - category (str): One of CATEGORIES
            - date_added (str): ISO date string
            - status (str): "active" or "answered"
            - date_answered (str|None): ISO date string or None
    """
    pass


def save_prayers(prayers):
    """Persist the prayer list to prayers.json.

    Args:
        prayers (list[dict]): The full prayer list to save.
    """
    pass


def add_prayer(text, category="other"):
    """Add a new prayer request to the list.

    Args:
        text (str): The prayer request text.
        category (str): Category from CATEGORIES. Defaults to "other".

    Returns:
        dict: The newly created prayer object.
    """
    pass


def remove_prayer(prayer_id):
    """Remove a prayer from the list entirely.

    Args:
        prayer_id (str): The UUID of the prayer to remove.

    Returns:
        bool: True if found and removed, False otherwise.
    """
    pass


def mark_answered(prayer_id):
    """Mark a prayer as answered.

    Args:
        prayer_id (str): The UUID of the prayer to mark.

    Returns:
        dict|None: The updated prayer object, or None if not found.
    """
    pass


def list_prayers(status="active"):
    """List prayers filtered by status.

    Args:
        status (str): Filter by "active", "answered", or "all".

    Returns:
        list[dict]: Filtered prayer objects.
    """
    pass


def format_review():
    """Format a weekly prayer review message for Telegram.

    Includes:
        - Count of active prayers by category
        - Any prayers answered this week
        - Encouragement message

    Returns:
        str: Formatted review message.
    """
    pass


def send_review():
    """Send the weekly prayer review via Telegram.

    Returns:
        bool: True if sent successfully.
    """
    pass


def main():
    """Entry point: parse CLI args and dispatch to the appropriate action."""
    pass


if __name__ == "__main__":
    main()
