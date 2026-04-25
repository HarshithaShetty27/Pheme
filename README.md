# AI Daily Digest

Free daily AI news aggregator that sends a digest to Discord.

## Sources
- **Anthropic Blog** — Claude releases and updates
- **OpenAI Blog** — GPT and OpenAI news
- **Google AI Blog** — Gemini, DeepMind updates
- **Hugging Face Blog** — Open source AI
- **Hacker News** — AI-filtered top stories
- **TechCrunch, The Verge, MIT Tech Review, Ars Technica** — AI journalism
- **GitHub Blog, Microsoft AI** — Developer tools
- **arXiv** — Latest AI/ML research papers

## Setup

### 1. Create a Discord Webhook
- Go to your Discord server → Server Settings → Integrations → Webhooks
- Click "New Webhook", pick a channel, copy the URL

### 2. Test locally
```bash
pip install -r requirements.txt
DISCORD_WEBHOOK_URL="your-webhook-url" python main.py
```

### 3. Deploy (GitHub Actions — free)
1. Push this repo to GitHub
2. Go to repo Settings → Secrets → Actions
3. Add secret: `DISCORD_WEBHOOK_URL` = your webhook URL
4. The digest runs daily at 8:00 AM UTC automatically
5. You can also trigger it manually from Actions tab → "Run workflow"

### Customize
- Edit `config.py` to add/remove RSS feeds, change arXiv categories, or adjust keywords
- Edit the cron schedule in `.github/workflows/daily-digest.yml`
