"""scripture.py — Daily verse selection and Telegram delivery.

Selects a verse from data/verses.json based on theme rotation,
delivers it via Telegram, and tracks sent verses to avoid repeats.

Themes: faith, hope, love, strength, peace, wisdom

Usage:
    python scripture.py          # Send today's verse
    python scripture.py --theme faith  # Send a verse from a specific theme

Cron: 0 6 * * * (6:00 AM daily)
"""

import argparse
import json
import os
import random
from datetime import date
from pathlib import Path

import requests

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
    with open(VERSES_FILE) as f:
        return json.load(f)["verses"]


def get_sent_verses():
    """Load the log of previously sent verse references.

    Returns:
        list[str]: List of verse references already sent.
    """
    if not SENT_LOG.exists():
        return []
    with open(SENT_LOG) as f:
        return json.load(f)


def mark_verse_sent(reference):
    """Record a verse reference as sent.

    Args:
        reference (str): The verse reference, e.g. "John 3:16"
    """
    sent = get_sent_verses()
    if reference not in sent:
        sent.append(reference)
    with open(SENT_LOG, "w") as f:
        json.dump(sent, f)


def select_verse(theme=None):
    """Select a verse that hasn't been sent yet.

    Uses theme rotation based on the day of the year if no theme
    is specified. Resets the sent log when all verses have been used.

    Args:
        theme (str, optional): Specific theme to select from.

    Returns:
        dict: The selected verse object.
    """
    verses = load_verses()
    sent = get_sent_verses()

    if theme is None:
        day = date.today().timetuple().tm_yday
        theme = THEMES[day % len(THEMES)]

    theme_verses = [v for v in verses if v["theme"] == theme]
    available = [v for v in theme_verses if v["reference"] not in sent]

    if not available:
        # All verses for this theme have been sent — reset only this theme's entries
        theme_refs = {v["reference"] for v in theme_verses}
        sent = [r for r in sent if r not in theme_refs]
        with open(SENT_LOG, "w") as f:
            json.dump(sent, f)
        available = theme_verses

    if not available:
        available = verses

    return random.choice(available)  # nosec B311 - non-cryptographic selection


_THEME_EMOJIS = {
    "faith": "✝️",
    "hope": "🕊️",
    "love": "❤️",
    "strength": "💪",
    "peace": "☮️",
    "wisdom": "📖",
}


def format_message(verse):
    """Format a verse into a Telegram-friendly message.

    Args:
        verse (dict): Verse object with reference, text, and theme.

    Returns:
        str: Formatted message string with emoji and attribution.
    """
    emoji = _THEME_EMOJIS.get(verse["theme"], "📖")
    return f"{emoji} *Daily Scripture*\n\n_{verse['text']}_\n\n— {verse['reference']}"


def send_to_telegram(message):
    """Send a message to the configured Telegram chat.

    Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment.

    Args:
        message (str): The message text to send.

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Error sending to Telegram: {e}")
        return False


def main():
    """Entry point: select today's verse and send it."""
    parser = argparse.ArgumentParser(description="Send daily scripture verse")
    parser.add_argument("--theme", choices=THEMES, help="Theme to select verse from")
    args = parser.parse_args()

    verse = select_verse(theme=args.theme)
    message = format_message(verse)
    print(message)
    mark_verse_sent(verse["reference"])
    send_to_telegram(message)


if __name__ == "__main__":
    main()
