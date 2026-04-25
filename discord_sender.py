"""Send formatted digest to Discord via webhook using embeds."""

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

WEEKEND_GREETINGS = [
    "Your weekly scrolls, assembled.",
    "A full week of whispers, condensed.",
    "Seven days. Here's what mattered.",
    "The week in review. The goddess remembers all.",
    "Sit back. This one covers the whole week.",
]

# Discord embed color palette
COLOR_BIG_NEWS = 0xFF4500   # red-orange — breaking / multi-source
COLOR_LABS = 0x7C3AED       # purple — from the labs
COLOR_NEWS = 0x2563EB       # blue — journalism
COLOR_DEV = 0x16A34A        # green — developer buzz
COLOR_RESEARCH = 0xF59E0B   # amber — papers
COLOR_LAUNCHES = 0xEC4899   # pink — product launches
COLOR_FOOTER = 0x6B7280     # gray


def _group_items(items, is_weekend=False):
    """Group items into categories, pulling out big news first."""
    big_news = []
    labs = []
    news = []
    dev_buzz = []
    research = []
    launches = []

    lab_sources = {"Anthropic", "OpenAI", "Google AI", "Hugging Face", "Microsoft AI"}
    news_sources = {"TechCrunch AI", "The Verge AI", "MIT Tech Review", "Ars Technica AI", "Wired AI", "VentureBeat AI"}
    dev_sources = {
        "Hacker News", "GitHub Blog",
        "r/MachineLearning", "r/LocalLLaMA", "r/singularity",
        "r/ChatGPT", "r/artificial", "r/ArtificialInteligence",
    }

    for item in items:
        # Stories covered by 3+ sources = big news
        if item.get("source_count", 1) >= 3:
            big_news.append(item)
            continue

        src = item["source"]
        if src in lab_sources:
            labs.append(item)
        elif src in news_sources:
            news.append(item)
        elif src in dev_sources:
            dev_buzz.append(item)
        elif src == "arXiv":
            research.append(item)
        elif src == "Product Hunt":
            launches.append(item)

    # Weekday caps vs weekend (more generous)
    if is_weekend:
        return {
            "big": big_news[:5],
            "labs": labs[:6],
            "news": news[:5],
            "dev": dev_buzz[:5],
            "research": research[:5],
            "launches": launches[:3],
        }
    return {
        "big": big_news[:3],
        "labs": labs[:4],
        "news": news[:3],
        "dev": dev_buzz[:3],
        "research": research[:3],
        "launches": launches[:2],
    }


def _format_item_line(item):
    """Format a single item as a markdown line."""
    title = item["title"]
    url = item["url"]
    sources = item.get("all_sources", [item["source"]])
    source_tag = ", ".join(sources) if len(sources) > 1 else sources[0]

    if url:
        return f"[{title}]({url}) — *{source_tag}*"
    return f"{title} — *{source_tag}*"


def _build_embed(title, items, color):
    """Build a Discord embed for a section."""
    description = "\n".join(f"- {_format_item_line(it)}" for it in items)
    return {
        "title": title,
        "description": description,
        "color": color,
    }


def build_embeds(items, is_weekend=False):
    """Build all embeds for the digest."""
    grouped = _group_items(items, is_weekend)
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    greetings = WEEKEND_GREETINGS if is_weekend else GREETINGS
    greeting = random.choice(greetings)

    embeds = []

    # Header embed
    title = "Weekend Recap" if is_weekend else date_str
    embeds.append({
        "title": title,
        "description": f"*{greeting}*",
        "color": COLOR_FOOTER,
    })

    if grouped["big"]:
        embeds.append(_build_embed("Big News", grouped["big"], COLOR_BIG_NEWS))

    if grouped["labs"]:
        embeds.append(_build_embed("From the Labs", grouped["labs"], COLOR_LABS))

    if grouped["news"]:
        embeds.append(_build_embed("In the News", grouped["news"], COLOR_NEWS))

    if grouped["dev"]:
        embeds.append(_build_embed("What Devs Are Talking About", grouped["dev"], COLOR_DEV))

    if grouped["launches"]:
        embeds.append(_build_embed("New Launches", grouped["launches"], COLOR_LAUNCHES))

    if grouped["research"]:
        embeds.append(_build_embed("Worth Reading", grouped["research"], COLOR_RESEARCH))

    # Footer
    embeds.append({
        "description": "— *Φήμη*",
        "color": COLOR_FOOTER,
    })

    return embeds


def send_to_discord(items, is_weekend=False):
    """Send the digest to Discord as embeds."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL environment variable not set!")
        return False

    if not items:
        payload = {
            "username": "Φήμη",
            "embeds": [{
                "description": "Nothing today. Even the goddess needs a day off.",
                "color": COLOR_FOOTER,
            }],
        }
        requests.post(webhook_url, json=payload, timeout=10)
        return True

    embeds = build_embeds(items, is_weekend)

    # Discord allows max 10 embeds per message, send in batches
    batch_size = 10
    total_batches = (len(embeds) + batch_size - 1) // batch_size
    print(f"Sending {len(embeds)} embeds in {total_batches} message(s)...")

    for i in range(0, len(embeds), batch_size):
        batch = embeds[i:i + batch_size]
        payload = {"username": "Φήμη", "embeds": batch}
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code not in (200, 204):
            print(f"  Failed: {resp.status_code} {resp.text}")
            return False
        batch_num = (i // batch_size) + 1
        print(f"  Sent batch {batch_num}/{total_batches}")

    print("Digest sent!")
    return True
