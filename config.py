"""
BountyPing Configuration
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database
DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "bountyping.db"))

# Scraping settings
SCRAPE_INTERVAL_MINUTES = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", 60))
USER_AGENT = "BountyPing/0.1 (Bug Bounty Aggregator; +https://bountyping.com)"
REQUEST_DELAY = float(os.environ.get("REQUEST_DELAY", 1.0))  # seconds between requests

# Notifications
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Flask
FLASK_PORT = int(os.environ.get("FLASK_PORT", 8080))
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

# Admin
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")

# Data sources
PROJECTDISCOVERY_JSON_URL = "https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/main/chaos-bugbounty-list.json"

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
