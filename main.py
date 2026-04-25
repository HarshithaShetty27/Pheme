#!/usr/bin/env python3
"""AI Daily Digest - Free daily AI news aggregator for Discord."""

from sources import fetch_all
from discord_sender import send_to_discord


def main():
    print("=" * 50)
    print("AI Daily Digest")
    print("=" * 50)

    items = fetch_all()
    print(f"\nTotal items collected: {len(items)}")

    if not items:
        print("No news found. Exiting.")
        return

    # Print summary to console
    print("\n--- Headlines ---")
    for item in items[:20]:
        print(f"  [{item['source']}] {item['title']}")

    # Send to Discord
    print("\n--- Sending to Discord ---")
    send_to_discord(items)


if __name__ == "__main__":
    main()
