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

import argparse
import json
import os
import random
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"
THEOLOGIANS_FILE = DATA_DIR / "theologians.json"
SENT_LOG = DATA_DIR / ".sent_quotes.json"

OPENCLAW_PORT = int(os.environ.get("OPENCLAW_PORT", "18790"))


def load_quotes():
    """Load all quotes from theologians.json.

    Returns:
        list[dict]: List of quote objects with keys:
            - text (str): The quote text
            - author (str): The theologian/philosopher
            - source (str, optional): Book or work title
            - theme (str): General theme of the quote
    """
    with open(THEOLOGIANS_FILE) as f:
        return json.load(f)["quotes"]


def get_sent_quotes():
    """Load the log of previously sent quote indices.

    Returns:
        list[int]: Indices of quotes already sent.
    """
    if not SENT_LOG.exists():
        return []
    with open(SENT_LOG) as f:
        return json.load(f)


def mark_quote_sent(index):
    """Record a quote index as sent.

    Args:
        index (int): The index of the sent quote.
    """
    sent = get_sent_quotes()
    if index not in sent:
        sent.append(index)
    with open(SENT_LOG, "w") as f:
        json.dump(sent, f)


def select_quote():
    """Select a quote that hasn't been sent yet.

    Resets the sent log when all quotes have been used.

    Returns:
        tuple[int, dict]: The index and quote object.
    """
    quotes = load_quotes()
    sent = get_sent_quotes()

    available = [i for i in range(len(quotes)) if i not in sent]

    if not available:
        # All quotes have been sent — reset and start over
        with open(SENT_LOG, "w") as f:
            json.dump([], f)
        available = list(range(len(quotes)))

    index = random.choice(available)  # nosec B311 - non-cryptographic selection
    return index, quotes[index]


def generate_reflection(quote):
    """Generate a reflection prompt using the OpenClaw gateway.

    Sends the quote to the local OpenClaw instance and asks for
    a brief reflection question or meditation prompt.

    Args:
        quote (dict): The quote object.

    Returns:
        str: A reflection prompt string.
    """
    prompt = (
        f'Given this quote by {quote["author"]}: "{quote["text"]}" '
        f'Provide a brief (2-3 sentence) reflection question or meditation prompt '
        f'for personal spiritual contemplation.'
    )
    payload = {
        "model": "openai-codex",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
    }
    url = f"http://localhost:{OPENCLAW_PORT}/v1/chat/completions"
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.RequestException as e:
        print(f"OpenClaw unavailable, skipping reflection: {e}")
        return None


def format_message(quote, reflection=None):
    """Format a quote and optional reflection into a Telegram message.

    Args:
        quote (dict): Quote object with text, author, and optional source.
        reflection (str, optional): Generated reflection prompt.

    Returns:
        str: Formatted message string.
    """
    source = quote.get("source", "")
    attribution = f"— {quote['author']}"
    if source and source != "attributed":
        attribution += f" ({source})"

    msg = f'💭 *Theological Reflection*\n\n_"{quote["text"]}"_\n\n{attribution}'
    if reflection:
        msg += f"\n\n*Reflect:* {reflection}"
    return msg


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
    """Entry point: select today's quote, generate reflection, and send."""
    parser = argparse.ArgumentParser(description="Send daily theological quote")
    parser.add_argument(
        "--quote-only", action="store_true",
        help="Send quote without reflection"
    )
    args = parser.parse_args()

    index, quote = select_quote()
    reflection = None if args.quote_only else generate_reflection(quote)
    message = format_message(quote, reflection)
    print(message)
    mark_quote_sent(index)
    send_to_telegram(message)


if __name__ == "__main__":
    main()
