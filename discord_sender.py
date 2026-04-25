"""Send formatted digest to Discord via webhook."""

import os
import random
from datetime import datetime, timezone

import requests

GREETINGS = [
    "Rise and shine, mortals.",
    "The goddess has heard things.",
    "Another day, another hundred breakthroughs.",
    "I listened to the internet so you don't have to.",
    "The whispers are loud today.",
    "Good morning. The machines have been busy.",
    "While you slept, things happened.",
    "The winds carry interesting news today.",
    "Olympus has new gossip.",
    "Your daily dose of 'the future is here'.",
    "I've been eavesdropping on the internet again.",
    "The scrolls are ready.",
    "Some mortals shipped code last night. Here's what matters.",
    "News travels fast. I travel faster.",
    "Grab your coffee. This one's good.",
]


def _pick_top_items(items, max_total=12):
    """Pick the most important items, keeping it digestible."""
    labs = []       # Anthropic, OpenAI, Google, HuggingFace, Microsoft
    news = []       # TechCrunch, Verge, MIT, Ars Technica
    dev_buzz = []   # Hacker News, GitHub
    research = []   # arXiv

    lab_sources = {"Anthropic", "OpenAI", "Google AI", "Hugging Face", "Microsoft AI"}
    news_sources = {"TechCrunch AI", "The Verge AI", "MIT Tech Review", "Ars Technica AI"}
    dev_sources = {"Hacker News", "GitHub Blog"}

    for item in items:
        src = item["source"]
        if src in lab_sources:
            labs.append(item)
        elif src in news_sources:
            news.append(item)
        elif src in dev_sources:
            dev_buzz.append(item)
        elif src == "arXiv":
            research.append(item)

    # Cap each section — keep it tight
    return {
        "labs": labs[:4],
        "news": news[:3],
        "dev": dev_buzz[:3],
        "research": research[:3],
    }


def format_digest(items):
    """Format items into a clean, readable digest."""
    if not items:
        return "Nothing today. Even the goddess needs a day off."

    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    greeting = random.choice(GREETINGS)
    grouped = _pick_top_items(items)

    lines = []
    lines.append(f"**{date_str}**")
    lines.append(f"*{greeting}*")
    lines.append("")

    if grouped["labs"]:
        lines.append("**From the Labs**")
        for item in grouped["labs"]:
            title = item["title"]
            url = item["url"]
            src = item["source"]
            if url:
                lines.append(f"[{title}]({url}) — {src}")
            else:
                lines.append(f"{title} — {src}")
        lines.append("")

    if grouped["news"]:
        lines.append("**In the News**")
        for item in grouped["news"]:
            title = item["title"]
            url = item["url"]
            src = item["source"]
            if url:
                lines.append(f"[{title}]({url}) — {src}")
            else:
                lines.append(f"{title} — {src}")
        lines.append("")

    if grouped["dev"]:
        lines.append("**What Devs Are Talking About**")
        for item in grouped["dev"]:
            title = item["title"]
            url = item["url"]
            if url:
                lines.append(f"[{title}]({url})")
            else:
                lines.append(title)
        lines.append("")

    if grouped["research"]:
        lines.append("**Worth Reading**")
        for item in grouped["research"]:
            title = item["title"]
            url = item["url"]
            if url:
                lines.append(f"[{title}]({url})")
            else:
                lines.append(title)
        lines.append("")

    lines.append("— *Φήμη*")

    return "\n".join(lines)


def send_to_discord(items):
    """Send the digest to Discord."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL environment variable not set!")
        return False

    message = format_digest(items)

    # Split if over Discord's 2000 char limit
    if len(message) <= 1900:
        chunks = [message]
    else:
        # Split at the last empty line before the limit
        mid = message[:1900].rfind("\n\n")
        if mid == -1:
            mid = 1900
        chunks = [message[:mid], message[mid:].strip()]

    print(f"Sending {len(chunks)} message(s) to Discord...")
    for i, chunk in enumerate(chunks):
        payload = {"content": chunk, "username": "Φήμη"}
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code not in (200, 204):
            print(f"  Failed: {resp.status_code} {resp.text}")
            return False
        print(f"  Sent {i+1}/{len(chunks)}")

    print("Digest sent!")
    return True
