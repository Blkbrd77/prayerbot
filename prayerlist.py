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
    python prayerlist.py --daily
    python prayerlist.py --set-theme monday "Intercession for family"
    python prayerlist.py --add-day-prayer monday "Pray for healing for mom"
    python prayerlist.py --show-day monday
    python prayerlist.py --poll-commands

Cron:
    0 4 * * * prayerlist.py --daily       (4:00 AM daily list)
    0 7 * * 0 prayerlist.py --review      (7:00 AM Sundays)
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
PRIVATE_DIR = Path(__file__).parent / ".private"
DAILY_PRAYER_FILE = Path(os.environ.get("PRAYER_DAILY_FILE", PRIVATE_DIR / "daily_prayers.json"))
COMMAND_STATE_FILE = Path(
    os.environ.get("PRAYER_COMMAND_STATE_FILE", PRIVATE_DIR / "command_state.json")
)

CATEGORIES = ["healing", "guidance", "gratitude", "family",
              "provision", "world", "personal", "other"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _default_daily_schedule():
    return {day: {"theme": "", "prayers": []} for day in DAYS}


def load_daily_schedule():
    """Load the private daily prayer schedule file."""
    if not DAILY_PRAYER_FILE.exists():
        return _default_daily_schedule()

    with open(DAILY_PRAYER_FILE) as f:
        data = json.load(f)

    schedule = _default_daily_schedule()
    for day in DAYS:
        day_data = data.get(day, {})
        schedule[day]["theme"] = str(day_data.get("theme", "")).strip()
        prayers = day_data.get("prayers", [])
        schedule[day]["prayers"] = [str(p).strip() for p in prayers if str(p).strip()]
    return schedule


def save_daily_schedule(schedule):
    """Persist the private daily prayer schedule file."""
    DAILY_PRAYER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DAILY_PRAYER_FILE, "w") as f:
        json.dump(schedule, f, indent=2)


def set_day_theme(day, theme):
    """Set the theme for a specific day."""
    day = day.lower()
    if day not in DAYS:
        raise ValueError(f"Invalid day: {day}")

    schedule = load_daily_schedule()
    schedule[day]["theme"] = theme.strip()
    save_daily_schedule(schedule)
    return schedule[day]


def add_day_prayer(day, text):
    """Add a prayer line item to a specific day."""
    day = day.lower()
    if day not in DAYS:
        raise ValueError(f"Invalid day: {day}")

    schedule = load_daily_schedule()
    schedule[day]["prayers"].append(text.strip())
    save_daily_schedule(schedule)
    return schedule[day]


def format_daily_prayer_list(target_date=None):
    """Format and return the prayer list for a given day."""
    target_date = target_date or date.today()
    day = DAYS[target_date.weekday()]
    entry = load_daily_schedule()[day]

    lines = [f"🙏 *Daily Prayer List — {day.capitalize()}*"]

    theme = entry.get("theme", "").strip()
    if theme:
        lines.append(f"\n*Theme:* {theme}")

    prayers = entry.get("prayers", [])
    if prayers:
        lines.append("\n*Prayers:*")
        for item in prayers:
            lines.append(f"• {item}")
    else:
        lines.append("\n_No prayers listed for today yet._")

    return "\n".join(lines)


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


def send_telegram_message(message, token=None, chat_id=None):
    """Send a message to the configured Telegram chat."""
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
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


def send_review():
    """Send the weekly prayer review via Telegram.

    Returns:
        bool: True if sent successfully.
    """
    message = format_review()
    print(message)
    return send_telegram_message(message)


def send_daily_list():
    """Send today's daily prayer list to Telegram."""
    message = format_daily_prayer_list()
    print(message)
    return send_telegram_message(message)


def load_command_state():
    if not COMMAND_STATE_FILE.exists():
        return {"last_update_id": 0}
    with open(COMMAND_STATE_FILE) as f:
        return json.load(f)


def save_command_state(state):
    COMMAND_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COMMAND_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def parse_command(text):
    """Parse Telegram command text into structured action."""
    parts = text.strip().split(maxsplit=2)
    if not parts:
        return None

    cmd = parts[0].lower()
    if cmd in ("/addprayer", "/add_prayer"):
        if len(parts) < 3:
            return None
        return {"action": "add_prayer", "day": parts[1].lower(), "text": parts[2].strip()}

    if cmd in ("/settheme", "/set_theme"):
        if len(parts) < 3:
            return None
        return {"action": "set_theme", "day": parts[1].lower(), "text": parts[2].strip()}

    return None


def poll_telegram_commands(max_updates=20):
    """Poll Telegram updates and apply prayer day commands."""
    token = os.environ.get("PRAYER_COMMAND_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN/PRAYER_COMMAND_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")
        return 0

    state = load_command_state()
    offset = int(state.get("last_update_id", 0)) + 1
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": offset, "limit": max_updates, "timeout": 10}
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        result = response.json().get("result", [])
    except requests.RequestException as e:
        print(f"Error polling Telegram updates: {e}")
        return 0

    processed = 0
    for update in result:
        update_id = int(update.get("update_id", 0))
        message = update.get("message") or {}
        incoming_chat = str((message.get("chat") or {}).get("id", ""))
        text = (message.get("text") or "").strip()

        state["last_update_id"] = max(int(state.get("last_update_id", 0)), update_id)
        if not text or incoming_chat != str(chat_id):
            continue

        parsed = parse_command(text)
        if not parsed:
            continue

        try:
            if parsed["action"] == "add_prayer":
                add_day_prayer(parsed["day"], parsed["text"])
                send_telegram_message(
                    f"Added prayer for {parsed['day'].capitalize()}: {parsed['text']}",
                    token=token,
                    chat_id=chat_id,
                )
                processed += 1
            elif parsed["action"] == "set_theme":
                set_day_theme(parsed["day"], parsed["text"])
                send_telegram_message(
                    f"Set theme for {parsed['day'].capitalize()}: {parsed['text']}",
                    token=token,
                    chat_id=chat_id,
                )
                processed += 1
        except ValueError:
            send_telegram_message(
                "Invalid day. Use monday, tuesday, wednesday, thursday, friday, saturday, or sunday.",
                token=token,
                chat_id=chat_id,
            )

    save_command_state(state)
    return processed


def main():
    """Entry point: parse CLI args and dispatch to the appropriate action."""
    parser = argparse.ArgumentParser(description="Prayer list manager")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", metavar="TEXT", help="Add a new prayer request")
    group.add_argument("--remove", metavar="ID", help="Remove a prayer by ID")
    group.add_argument("--answered", metavar="ID", help="Mark a prayer as answered")
    group.add_argument("--list", action="store_true", help="List active prayers")
    group.add_argument("--review", action="store_true", help="Send weekly review")
    group.add_argument("--daily", action="store_true", help="Send today's daily prayer list")
    group.add_argument(
        "--set-theme", nargs=2, metavar=("DAY", "THEME"),
        help="Set theme for a specific day"
    )
    group.add_argument(
        "--add-day-prayer", nargs=2, metavar=("DAY", "TEXT"),
        help="Add a prayer line item to a specific day"
    )
    group.add_argument("--show-day", metavar="DAY", help="Show schedule for one day")
    group.add_argument(
        "--poll-commands", action="store_true",
        help="Poll Telegram for /addprayer and /settheme commands"
    )
    parser.add_argument(
        "--category", choices=CATEGORIES, default="other",
        help="Category for --add"
    )
    parser.add_argument(
        "--max-updates", type=int, default=20,
        help="Max updates to fetch when using --poll-commands"
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
    elif args.daily:
        send_daily_list()
    elif args.set_theme:
        day, theme = args.set_theme[0].lower(), args.set_theme[1]
        try:
            set_day_theme(day, theme)
            print(f"Set {day.capitalize()} theme to: {theme}")
        except ValueError as e:
            print(str(e))
    elif args.add_day_prayer:
        day, text = args.add_day_prayer[0].lower(), args.add_day_prayer[1]
        try:
            add_day_prayer(day, text)
            print(f"Added to {day.capitalize()}: {text}")
        except ValueError as e:
            print(str(e))
    elif args.show_day:
        day = args.show_day.lower()
        if day not in DAYS:
            print(f"Invalid day: {day}")
        else:
            schedule = load_daily_schedule()[day]
            print(f"{day.capitalize()} theme: {schedule['theme'] or '(none)'}")
            if schedule["prayers"]:
                for item in schedule["prayers"]:
                    print(f"- {item}")
            else:
                print("No prayers for this day yet.")
    elif args.poll_commands:
        processed = poll_telegram_commands(max_updates=args.max_updates)
        print(f"Processed {processed} command(s).")


if __name__ == "__main__":
    main()
