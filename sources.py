"""Fetch news from various free sources."""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape

import feedparser
import requests

from config import (
    AI_KEYWORDS,
    ARXIV_CATEGORIES,
    ARXIV_MAX_RESULTS,
    HN_ITEM_URL,
    HN_TOP_N,
    HN_TOP_STORIES_URL,
    LOOKBACK_HOURS,
    RSS_FEEDS,
)


def _is_recent(dt, cutoff):
    """Check if a datetime is after the cutoff."""
    if dt is None:
        return True  # if no date, include it (better to over-include)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff


def _clean_html(text):
    """Strip HTML tags and decode entities."""
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300]  # cap description length


def fetch_rss_feeds(cutoff):
    """Fetch articles from RSS feeds published after cutoff."""
    articles = []
    for feed_conf in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_conf["url"])
            for entry in feed.entries[:15]:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                if not _is_recent(published, cutoff):
                    continue

                description = ""
                if hasattr(entry, "summary"):
                    description = _clean_html(entry.summary)

                articles.append({
                    "title": entry.get("title", "No title"),
                    "url": entry.get("link", ""),
                    "description": description,
                    "source": feed_conf["tag"],
                    "published": published,
                })
        except Exception as e:
            print(f"  Warning: Failed to fetch {feed_conf['tag']}: {e}")
    return articles


def fetch_arxiv_papers(cutoff):
    """Fetch recent AI papers from arXiv."""
    papers = []
    cat_query = "+OR+".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={cat_query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={ARXIV_MAX_RESULTS}"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            link = entry.find("atom:id", ns)
            published = entry.find("atom:published", ns)

            pub_dt = None
            if published is not None and published.text:
                pub_dt = datetime.fromisoformat(published.text.replace("Z", "+00:00"))

            title_text = title.text.strip().replace("\n", " ") if title is not None else "No title"
            summary_text = _clean_html(summary.text) if summary is not None else ""
            link_text = link.text if link is not None else ""

            papers.append({
                "title": title_text,
                "url": link_text,
                "description": summary_text,
                "source": "arXiv",
                "published": pub_dt,
            })
    except Exception as e:
        print(f"  Warning: Failed to fetch arXiv: {e}")
    return papers


def fetch_hacker_news(cutoff):
    """Fetch AI-related stories from Hacker News top stories."""
    stories = []
    try:
        resp = requests.get(HN_TOP_STORIES_URL, timeout=10)
        resp.raise_for_status()
        top_ids = resp.json()[:HN_TOP_N]

        for story_id in top_ids:
            try:
                item_resp = requests.get(HN_ITEM_URL.format(story_id), timeout=5)
                item = item_resp.json()
                if not item or item.get("type") != "story":
                    continue

                title = item.get("title", "")
                title_lower = title.lower()

                # Check if AI-related
                if not any(kw in title_lower for kw in AI_KEYWORDS):
                    continue

                pub_dt = datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc)
                if not _is_recent(pub_dt, cutoff):
                    continue

                url = item.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                stories.append({
                    "title": title,
                    "url": url,
                    "description": f"Score: {item.get('score', 0)} | Comments: {item.get('descendants', 0)}",
                    "source": "Hacker News",
                    "published": pub_dt,
                })
            except Exception:
                continue
            time.sleep(0.1)  # be nice to HN API
    except Exception as e:
        print(f"  Warning: Failed to fetch Hacker News: {e}")
    return stories


def fetch_all():
    """Fetch from all sources and return combined list."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    print(f"Fetching news since {cutoff.strftime('%Y-%m-%d %H:%M UTC')}...")

    print("  Fetching RSS feeds...")
    articles = fetch_rss_feeds(cutoff)
    print(f"  Got {len(articles)} RSS articles")

    print("  Fetching arXiv papers...")
    papers = fetch_arxiv_papers(cutoff)
    print(f"  Got {len(papers)} arXiv papers")

    print("  Fetching Hacker News...")
    hn = fetch_hacker_news(cutoff)
    print(f"  Got {len(hn)} HN stories")

    all_items = articles + papers + hn

    # Deduplicate by title similarity
    seen_titles = set()
    unique = []
    for item in all_items:
        key = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(item)

    # Sort: Anthropic/Claude first, then by source priority
    source_priority = {
        "Anthropic": 0,
        "OpenAI": 1,
        "Google AI": 1,
        "Hugging Face": 2,
        "Hacker News": 3,
        "TechCrunch AI": 4,
        "The Verge AI": 4,
        "MIT Tech Review": 4,
        "Ars Technica AI": 4,
        "GitHub Blog": 5,
        "Microsoft AI": 5,
        "arXiv": 6,
    }
    unique.sort(key=lambda x: (source_priority.get(x["source"], 99)))

    return unique
