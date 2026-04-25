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
    PRODUCTHUNT_RSS,
    REDDIT_SUBS,
    REDDIT_TOP_N,
    RSS_FEEDS,
)


def _is_recent(dt, cutoff):
    """Check if a datetime is after the cutoff."""
    if dt is None:
        return True
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
    return text[:300]


def _normalize_title(title):
    """Normalize a title for dedup comparison."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


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
            time.sleep(0.1)
    except Exception as e:
        print(f"  Warning: Failed to fetch Hacker News: {e}")
    return stories


def fetch_reddit(cutoff):
    """Fetch top AI posts from Reddit (public JSON, no auth)."""
    posts = []
    headers = {"User-Agent": "PhemeDigest/1.0"}
    for sub_conf in REDDIT_SUBS:
        try:
            url = f"https://www.reddit.com/r/{sub_conf['sub']}/hot.json?limit={REDDIT_TOP_N}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                if post.get("stickied"):
                    continue

                pub_dt = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)
                if not _is_recent(pub_dt, cutoff):
                    continue

                title = post.get("title", "")
                post_url = post.get("url", "")
                if not post_url.startswith("http"):
                    post_url = f"https://reddit.com{post.get('permalink', '')}"

                posts.append({
                    "title": title,
                    "url": post_url,
                    "description": f"Upvotes: {post.get('ups', 0)} | Comments: {post.get('num_comments', 0)}",
                    "source": sub_conf["tag"],
                    "published": pub_dt,
                })
            time.sleep(1)  # respect reddit rate limits
        except Exception as e:
            print(f"  Warning: Failed to fetch {sub_conf['tag']}: {e}")
    return posts


def fetch_producthunt(cutoff):
    """Fetch AI-related launches from Product Hunt RSS."""
    launches = []
    try:
        feed = feedparser.parse(PRODUCTHUNT_RSS)
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            title_lower = title.lower()

            if not any(kw in title_lower for kw in AI_KEYWORDS):
                continue

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            if not _is_recent(published, cutoff):
                continue

            description = ""
            if hasattr(entry, "summary"):
                description = _clean_html(entry.summary)

            launches.append({
                "title": title,
                "url": entry.get("link", ""),
                "description": description,
                "source": "Product Hunt",
                "published": published,
            })
    except Exception as e:
        print(f"  Warning: Failed to fetch Product Hunt: {e}")
    return launches


def _deduplicate(items):
    """Smart dedup: merge stories covered by multiple sources."""
    # Build clusters of similar titles
    clusters = []  # list of {"items": [...], "canonical": item}

    for item in items:
        norm = _normalize_title(item["title"])
        words = set(norm.split())

        matched = False
        for cluster in clusters:
            canon_norm = _normalize_title(cluster["canonical"]["title"])
            canon_words = set(canon_norm.split())

            # Check word overlap — if 60%+ of the shorter title's words match, it's the same story
            if not canon_words or not words:
                continue
            shorter = min(len(words), len(canon_words))
            overlap = len(words & canon_words)
            if overlap >= max(3, shorter * 0.6):
                cluster["items"].append(item)
                matched = True
                break

        if not matched:
            clusters.append({"items": [item], "canonical": item})

    # For each cluster, pick the best item and note all sources
    deduped = []
    for cluster in clusters:
        all_sources = list({it["source"] for it in cluster["items"]})
        best = cluster["canonical"]
        best["all_sources"] = all_sources
        best["source_count"] = len(all_sources)
        deduped.append(best)

    return deduped


def fetch_all(lookback_hours=None):
    """Fetch from all sources and return deduplicated list."""
    from config import LOOKBACK_HOURS
    hours = lookback_hours or LOOKBACK_HOURS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
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

    print("  Fetching Reddit...")
    reddit = fetch_reddit(cutoff)
    print(f"  Got {len(reddit)} Reddit posts")

    print("  Fetching Product Hunt...")
    ph = fetch_producthunt(cutoff)
    print(f"  Got {len(ph)} Product Hunt launches")

    all_items = articles + papers + hn + reddit + ph

    # Deduplicate with smart merging
    deduped = _deduplicate(all_items)
    print(f"  After dedup: {len(deduped)} unique stories (from {len(all_items)} total)")

    # Sort: multi-source stories first (big news), then by source priority
    source_priority = {
        "Anthropic": 0, "OpenAI": 1, "Google AI": 1,
        "Hugging Face": 2, "r/MachineLearning": 3, "r/LocalLLaMA": 3,
        "r/singularity": 3, "r/ChatGPT": 3, "r/artificial": 3,
        "r/ArtificialInteligence": 3,
        "Hacker News": 4, "TechCrunch AI": 5, "The Verge AI": 5,
        "MIT Tech Review": 5, "Ars Technica AI": 5,
        "Wired AI": 5, "VentureBeat AI": 5,
        "GitHub Blog": 6, "Microsoft AI": 6,
        "Product Hunt": 7, "arXiv": 8,
    }
    deduped.sort(key=lambda x: (-x.get("source_count", 1), source_priority.get(x["source"], 99)))

    return deduped
