"""theologian.py — Daily theological quote and reflection prompt.

Selects a quote from data/theologians.json, optionally generates
a brief reflection prompt via the OpenClaw gateway, and delivers
both via Telegram.

Sources: Augustine, Aquinas, C.S. Lewis, Bonhoeffer, Kierkegaard,
         Pascal, Chesterton, Spurgeon, Tozer, and more.

Usage:
    python theologian.py          # Send today's quote + reflection
    python theologian.py --quote-only  # Send quote without reflection

Cron: 0 20 * * * (8:00 PM daily)
"""

import json
import os
import random
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
THEOLOGIANS_FILE = DATA_DIR / "theologians.json"
SENT_LOG = DATA_DIR / ".sent_quotes.json"

OPENCLAW_PORT = 18790


def load_quotes():
    """Load all quotes from theologians.json.

    Returns:
        list[dict]: List of quote objects with keys:
            - text (str): The quote text
            - author (str): The theologian/philosopher
            - source (str, optional): Book or work title
            - theme (str): General theme of the quote
    """
    pass


def get_sent_quotes():
    """Load the log of previously sent quote indices.

    Returns:
        list[int]: Indices of quotes already sent.
    """
    pass


def mark_quote_sent(index):
    """Record a quote index as sent.

    Args:
        index (int): The index of the sent quote.
    """
    pass


def select_quote():
    """Select a quote that hasn't been sent yet.

    Resets the sent log when all quotes have been used.

    Returns:
        tuple[int, dict]: The index and quote object.
    """
    pass


def generate_reflection(quote):
    """Generate a reflection prompt using the OpenClaw gateway.

    Sends the quote to the local OpenClaw instance and asks for
    a brief reflection question or meditation prompt.

    Args:
        quote (dict): The quote object.

    Returns:
        str: A reflection prompt string.
    """
    pass


def format_message(quote, reflection=None):
    """Format a quote and optional reflection into a Telegram message.

    Args:
        quote (dict): Quote object with text, author, and optional source.
        reflection (str, optional): Generated reflection prompt.

    Returns:
        str: Formatted message string.
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
    """Entry point: select today's quote, generate reflection, and send."""
    pass


if __name__ == "__main__":
    main()
