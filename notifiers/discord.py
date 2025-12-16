"""
Discord webhook notifications for BountyPing
"""

import logging
import requests
from typing import Optional

from db.models import Program
from config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Send notifications via Discord webhook"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL

    def send_new_program(self, program: Program) -> bool:
        """Notify about a new bug bounty program"""
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        # Build embed
        embed = {
            "title": f"🆕 New Bug Bounty: {program.name}",
            "url": program.url,
            "color": 0x00ff00,  # Green
            "fields": [
                {
                    "name": "Platform",
                    "value": program.platform.title(),
                    "inline": True
                },
                {
                    "name": "Bounty",
                    "value": program.bounty_range,
                    "inline": True
                }
            ],
            "footer": {
                "text": "BountyPing"
            }
        }

        # Add asset types if available
        if program.asset_types:
            embed["fields"].append({
                "name": "Asset Types",
                "value": ", ".join(program.asset_types),
                "inline": False
            })

        # Add scope preview if available
        if program.assets:
            scope_preview = ", ".join(program.assets[:5])
            if len(program.assets) > 5:
                scope_preview += f" (+{len(program.assets) - 5} more)"
            embed["fields"].append({
                "name": "Scope Preview",
                "value": f"`{scope_preview}`",
                "inline": False
            })

        payload = {
            "embeds": [embed]
        }

        return self._send_webhook(payload)

    def send_updated_program(self, program: Program) -> bool:
        """Notify about an updated program"""
        if not self.webhook_url:
            return False

        embed = {
            "title": f"📝 Updated: {program.name}",
            "url": program.url,
            "color": 0xffa500,  # Orange
            "fields": [
                {
                    "name": "Platform",
                    "value": program.platform.title(),
                    "inline": True
                },
                {
                    "name": "Bounty",
                    "value": program.bounty_range,
                    "inline": True
                }
            ],
            "footer": {
                "text": "BountyPing"
            }
        }

        payload = {
            "embeds": [embed]
        }

        return self._send_webhook(payload)

    def send_batch_summary(self, new_count: int, updated_count: int, platform: str) -> bool:
        """Send a summary of scraping results"""
        if not self.webhook_url or (new_count == 0 and updated_count == 0):
            return False

        message = f"**{platform.title()} Scrape Complete**\n"
        if new_count > 0:
            message += f"🆕 {new_count} new program(s)\n"
        if updated_count > 0:
            message += f"📝 {updated_count} updated program(s)"

        payload = {
            "content": message
        }

        return self._send_webhook(payload)

    def _send_webhook(self, payload: dict) -> bool:
        """Send payload to Discord webhook"""
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Discord notification sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
