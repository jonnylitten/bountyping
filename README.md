# BountyPing 🎯

**All bug bounty programs in one place.**

BountyPing aggregates bug bounty programs from multiple platforms (HackerOne, Bugcrowd, Immunefi, etc.) into a single, searchable interface with Discord notifications for new programs.

Part of the *Ping family: RegPing, GovPing, GrantPing.

---

## Features

- 🔍 **Unified Search** - Browse programs from all major platforms in one place
- 🎯 **Smart Filtering** - Filter by platform, bounty amount, asset type, and more
- 🔔 **Discord Notifications** - Get alerts when new programs launch or existing ones update
- 📊 **Clean UI** - Simple, fast web interface
- 🤖 **Auto-Scraping** - Background jobs keep data fresh
- 💾 **SQLite** - Lightweight, zero-config database

---

## Quick Start

### 1. Install Dependencies

```bash
cd bountyping
pip install -r requirements.txt
```

### 2. Seed Database

Get a quick start with hundreds of programs from ProjectDiscovery:

```bash
python cli.py seed
```

### 3. Configure Notifications (Optional)

Create a `.env` file:

```bash
cp .env.example .env
```

Add your Discord webhook URL:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

### 4. Run BountyPing

```bash
python run.py
```

This starts:
- Web UI at http://localhost:8080
- Background scraper (runs every hour by default)

---

## CLI Usage

BountyPing includes a CLI for manual operations:

### Seed Database
```bash
python cli.py seed
```

### Scrape Specific Platform
```bash
python cli.py scrape hackerone
python cli.py scrape hackerone --notify  # Send Discord notification
```

### View Statistics
```bash
python cli.py stats
```

### Search Programs
```bash
python cli.py search --platform hackerone
python cli.py search --min-bounty 10000
python cli.py search --search "api" --bounties-only
```

### View Scrape Logs
```bash
python cli.py logs --limit 10
```

---

## Configuration

All configuration is done via environment variables (or `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_PATH` | SQLite database path | `bountyping.db` |
| `SCRAPE_INTERVAL_MINUTES` | How often to scrape | `60` |
| `REQUEST_DELAY` | Delay between requests (seconds) | `1.0` |
| `DISCORD_WEBHOOK_URL` | Discord webhook for notifications | - |
| `FLASK_HOST` | Web app host | `0.0.0.0` |
| `FLASK_PORT` | Web app port | `8080` |
| `ADMIN_SECRET` | Secret for admin endpoints | - |

---

## Supported Platforms

### Currently Implemented
- ✅ **HackerOne** - Live GraphQL scraper
- ✅ **ProjectDiscovery Seed** - 400+ programs from GitHub list

### Planned
- 🔜 Bugcrowd
- 🔜 Intigriti
- 🔜 YesWeHack
- 🔜 Immunefi
- 🔜 Code4rena
- 🔜 Huntr
- 🔜 Algora

---

## API Endpoints

### `GET /api/programs`
Get all programs with filters.

**Query params:**
- `platform` - Filter by platform
- `min_bounty` - Minimum bounty amount
- `asset_type` - Filter by asset type (web, mobile, api, etc.)
- `search` - Search in name/slug
- `sort_by` - Sort order (newest, bounty, name)
- `new_only` - Only show programs from last 7 days (true/false)
- `bounties_only` - Only show paid programs (true/false)

**Example:**
```bash
curl "http://localhost:8080/api/programs?platform=hackerone&min_bounty=5000&bounties_only=true"
```

### `GET /api/stats`
Get database statistics.

### `GET /api/platforms`
Get list of all platforms with program counts.

### `GET /health`
Health check endpoint.

---

## Deployment

### Railway (Recommended)

1. Create new project on Railway
2. Connect your GitHub repo
3. Set environment variables in Railway dashboard
4. Deploy!

Railway will automatically detect the Python app and install dependencies.

**Procfile:**
```
web: python run.py
```

### Fly.io

```bash
fly launch
fly secrets set DISCORD_WEBHOOK_URL=your-webhook-url
fly deploy
```

### Docker

```bash
docker build -t bountyping .
docker run -p 8080:8080 -e DISCORD_WEBHOOK_URL=your-webhook bountyping
```

### VPS ($5/month)

```bash
# Install Python 3.11+
apt install python3 python3-pip

# Clone repo
git clone your-repo
cd bountyping

# Install deps
pip install -r requirements.txt

# Seed database
python cli.py seed

# Run with systemd or screen
screen -S bountyping
python run.py
```

---

## Architecture

```
bountyping/
├── scrapers/          # Platform scrapers
│   ├── base.py        # Base scraper class
│   ├── hackerone.py   # HackerOne GraphQL scraper
│   └── projectdiscovery.py  # Seed from GitHub JSON
├── db/                # Database layer
│   ├── models.py      # Data models
│   └── database.py    # SQLite operations
├── notifiers/         # Notification services
│   └── discord.py     # Discord webhooks
├── web/               # Flask web app
│   ├── app.py         # Flask routes
│   ├── templates/     # HTML templates
│   └── static/        # CSS/JS
├── config.py          # Configuration
├── scheduler.py       # Background scraping loop
├── cli.py             # Command-line interface
├── run.py             # Main entry point
└── requirements.txt
```

---

## Contributing

Want to add a new platform scraper?

1. Create `scrapers/yourplatform.py`
2. Extend `BaseScraper`
3. Implement `scrape_programs()` method
4. Add to `scheduler.py`
5. Test with `python cli.py scrape yourplatform`

---

## Roadmap

**v0.1 (MVP)** ✅
- [x] HackerOne scraper
- [x] ProjectDiscovery seed
- [x] SQLite database
- [x] Web UI with filtering
- [x] Discord notifications
- [x] CLI tools

**v0.2 (More Platforms)**
- [ ] Bugcrowd scraper
- [ ] Intigriti scraper
- [ ] YesWeHack scraper
- [ ] Telegram notifications

**v0.3 (Advanced Features)**
- [ ] User accounts / saved searches
- [ ] Email notifications
- [ ] RSS feeds
- [ ] Advanced filters (tech stack, rewards type)

**v0.4 (Polish)**
- [ ] Better mobile UI
- [ ] Program change history
- [ ] Analytics dashboard
- [ ] API rate limiting

---

## License

MIT

---

## Credits

Built with the Ping philosophy: aggregate fragmented public data, make it searchable, notify on changes.

Data sources:
- [ProjectDiscovery/public-bugbounty-programs](https://github.com/projectdiscovery/public-bugbounty-programs)
- Platform public directories (HackerOne, Bugcrowd, etc.)

---

**Made with ☕ by Jonny**
