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

import argparse
import json
import os
import uuid
from datetime import date, timedelta
from pathlib import Path

import requests

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
    if not PRAYERS_FILE.exists():
        return []
    with open(PRAYERS_FILE) as f:
        return json.load(f).get("prayers", [])


def save_prayers(prayers):
    """Persist the prayer list to prayers.json.

    Args:
        prayers (list[dict]): The full prayer list to save.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PRAYERS_FILE, "w") as f:
        json.dump({"prayers": prayers}, f, indent=2)


def add_prayer(text, category="other"):
    """Add a new prayer request to the list.

    Args:
        text (str): The prayer request text.
        category (str): Category from CATEGORIES. Defaults to "other".

    Returns:
        dict: The newly created prayer object.
    """
    prayers = load_prayers()
    prayer = {
        "id": str(uuid.uuid4()),
        "text": text,
        "category": category if category in CATEGORIES else "other",
        "date_added": date.today().isoformat(),
        "status": "active",
        "date_answered": None,
    }
    prayers.append(prayer)
    save_prayers(prayers)
    return prayer


def remove_prayer(prayer_id):
    """Remove a prayer from the list entirely.

    Args:
        prayer_id (str): The UUID of the prayer to remove.

    Returns:
        bool: True if found and removed, False otherwise.
    """
    prayers = load_prayers()
    new_prayers = [p for p in prayers if p["id"] != prayer_id]
    if len(new_prayers) == len(prayers):
        return False
    save_prayers(new_prayers)
    return True


def mark_answered(prayer_id):
    """Mark a prayer as answered.

    Args:
        prayer_id (str): The UUID of the prayer to mark.

    Returns:
        dict|None: The updated prayer object, or None if not found.
    """
    prayers = load_prayers()
    for prayer in prayers:
        if prayer["id"] == prayer_id:
            prayer["status"] = "answered"
            prayer["date_answered"] = date.today().isoformat()
            save_prayers(prayers)
            return prayer
    return None


def list_prayers(status="active"):
    """List prayers filtered by status.

    Args:
        status (str): Filter by "active", "answered", or "all".

    Returns:
        list[dict]: Filtered prayer objects.
    """
    prayers = load_prayers()
    if status == "all":
        return prayers
    return [p for p in prayers if p["status"] == status]


def format_review():
    """Format a weekly prayer review message for Telegram.

    Includes:
        - Count of active prayers by category
        - Any prayers answered this week
        - Encouragement message

    Returns:
        str: Formatted review message.
    """
    prayers = load_prayers()
    active = [p for p in prayers if p["status"] == "active"]

    category_counts = {}
    for p in active:
        cat = p["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    week_ago = (date.today() - timedelta(days=7)).isoformat()
    answered_this_week = [
        p for p in prayers
        if p["status"] == "answered"
        and p.get("date_answered") is not None
        and p["date_answered"] >= week_ago
    ]

    lines = ["🙏 *Weekly Prayer Review*\n"]

    if active:
        lines.append(f"*Active Prayers:* {len(active)}")
        for cat, count in sorted(category_counts.items()):
            lines.append(f"  • {cat.capitalize()}: {count}")
    else:
        lines.append("No active prayers.")

    if answered_this_week:
        lines.append(f"\n*Answered This Week:* {len(answered_this_week)}")
        for p in answered_this_week:
            lines.append(f"  ✅ {p['text']}")

    lines.append(
        "\n_'The prayer of a righteous person is powerful and effective.' — James 5:16_"
    )

    return "\n".join(lines)


def send_review():
    """Send the weekly prayer review via Telegram.

    Returns:
        bool: True if sent successfully.
    """
    message = format_review()
    print(message)

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
    """Entry point: parse CLI args and dispatch to the appropriate action."""
    parser = argparse.ArgumentParser(description="Prayer list manager")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", metavar="TEXT", help="Add a new prayer request")
    group.add_argument("--remove", metavar="ID", help="Remove a prayer by ID")
    group.add_argument("--answered", metavar="ID", help="Mark a prayer as answered")
    group.add_argument("--list", action="store_true", help="List active prayers")
    group.add_argument("--review", action="store_true", help="Send weekly review")
    parser.add_argument(
        "--category", choices=CATEGORIES, default="other",
        help="Category for --add"
    )
    args = parser.parse_args()

    if args.add:
        prayer = add_prayer(args.add, args.category)
        print(f"Added prayer [{prayer['id'][:8]}]: {prayer['text']}")
    elif args.remove:
        success = remove_prayer(args.remove)
        print("Removed." if success else "Prayer not found.")
    elif args.answered:
        prayer = mark_answered(args.answered)
        if prayer:
            print(f"Marked answered: {prayer['text']}")
        else:
            print("Prayer not found.")
    elif args.list:
        prayers = list_prayers("active")
        if not prayers:
            print("No active prayers.")
        else:
            for p in prayers:
                print(f"[{p['id'][:8]}] ({p['category']}) {p['text']} — added {p['date_added']}")
    elif args.review:
        send_review()


if __name__ == "__main__":
    main()
