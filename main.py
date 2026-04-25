#!/usr/bin/env python3
"""AI Daily Digest - Free daily AI news aggregator for Discord."""

from datetime import datetime, timezone

from config import LOOKBACK_HOURS, WEEKLY_LOOKBACK_HOURS
from sources import fetch_all
from discord_sender import send_to_discord


def main():
    today = datetime.now(timezone.utc)
    is_sunday = today.weekday() == 6

    if is_sunday:
        print("=" * 50)
        print("Φήμη — Weekend Recap")
        print("=" * 50)
        items = fetch_all(lookback_hours=WEEKLY_LOOKBACK_HOURS)
    else:
        print("=" * 50)
        print("Φήμη — Daily Digest")
        print("=" * 50)
        items = fetch_all(lookback_hours=LOOKBACK_HOURS)

    print(f"\nTotal items collected: {len(items)}")

    if not items:
        print("No news found. Exiting.")
        return

    # Show big news in console
    big = [it for it in items if it.get("source_count", 1) >= 3]
    if big:
        print(f"\n--- Big News ({len(big)} stories covered by 3+ sources) ---")
        for item in big:
            sources = ", ".join(item.get("all_sources", []))
            print(f"  [{sources}] {item['title']}")

    print(f"\n--- All Headlines ---")
    for item in items[:25]:
        count = item.get("source_count", 1)
        tag = f"x{count} " if count > 1 else ""
        print(f"  {tag}[{item['source']}] {item['title']}")

    print(f"\n--- Sending to Discord ---")
    send_to_discord(items, is_weekend=is_sunday)


if __name__ == "__main__":
    main()
