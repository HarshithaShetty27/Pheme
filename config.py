"""Configuration for AI Daily Digest."""

# RSS feeds to monitor
RSS_FEEDS = [
    # Anthropic / Claude
    {"url": "https://www.anthropic.com/rss.xml", "tag": "Anthropic"},

    # OpenAI
    {"url": "https://openai.com/blog/rss.xml", "tag": "OpenAI"},

    # Google AI / DeepMind
    {"url": "https://blog.google/technology/ai/rss/", "tag": "Google AI"},

    # AI / Tech news outlets
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "tag": "TechCrunch AI"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "tag": "The Verge AI"},
    {"url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "tag": "MIT Tech Review"},
    {"url": "https://arstechnica.com/ai/feed/", "tag": "Ars Technica AI"},
    {"url": "https://www.wired.com/feed/tag/ai/latest/rss", "tag": "Wired AI"},
    {"url": "https://venturebeat.com/category/ai/feed/", "tag": "VentureBeat AI"},

    # Developer-focused
    {"url": "https://github.blog/feed/", "tag": "GitHub Blog"},
    {"url": "https://devblogs.microsoft.com/ai/feed/", "tag": "Microsoft AI"},
    {"url": "https://huggingface.co/blog/feed.xml", "tag": "Hugging Face"},
]

# Reddit - public JSON API, no auth needed
REDDIT_SUBS = [
    {"sub": "LocalLLaMA", "tag": "r/LocalLLaMA"},
    {"sub": "MachineLearning", "tag": "r/MachineLearning"},
    {"sub": "singularity", "tag": "r/singularity"},
    {"sub": "ChatGPT", "tag": "r/ChatGPT"},
    {"sub": "artificial", "tag": "r/artificial"},
    {"sub": "ArtificialInteligence", "tag": "r/ArtificialInteligence"},
]
REDDIT_TOP_N = 10  # top posts per sub

# Product Hunt - tech launches
PRODUCTHUNT_RSS = "https://www.producthunt.com/feed"

# arXiv categories to search
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]
ARXIV_MAX_RESULTS = 10

# Hacker News
HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
HN_TOP_N = 50  # check top 50 stories for AI relevance

# AI keywords for filtering HN, Reddit, Product Hunt
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "anthropic", "openai",
    "gemini", "google ai", "deepmind", "meta ai", "llama", "mistral",
    "transformer", "neural network", "diffusion", "stable diffusion",
    "midjourney", "copilot", "chatgpt", "agent", "rag", "fine-tune",
    "fine-tuning", "embedding", "vector database", "hugging face",
    "open source ai", "model", "benchmark", "reasoning", "multimodal",
    "computer vision", "nlp", "natural language", "robotics",
    "autonomous", "self-driving", "nvidia", "cuda", "gpu", "tpu",
    "api", "sdk", "developer tool", "coding assistant", "devin",
    "cursor", "programming", "software engineer",
]

# How many hours back to look for news (25h to avoid gaps)
LOOKBACK_HOURS = 25

# Weekend recap looks back over the full week
WEEKLY_LOOKBACK_HOURS = 170  # ~7 days
