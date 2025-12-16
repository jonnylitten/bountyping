"""
BountyPing Scheduler

Runs scrapers periodically and sends notifications.
"""

import logging
import time
import threading
from datetime import datetime

from config import DB_PATH, SCRAPE_INTERVAL_MINUTES
from db.database import BountyDatabase
from scrapers.hackerone import HackerOneScraper
from scrapers.projectdiscovery import ProjectDiscoveryScraper
from notifiers.discord import DiscordNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BountyPingScheduler:
    """Manages periodic scraping and notifications"""

    def __init__(self, db_path: str = DB_PATH):
        self.db = BountyDatabase(db_path)
        self.notifier = DiscordNotifier()
        self.scrapers = {
            'hackerone': HackerOneScraper(self.db),
            # Add more scrapers here as they're implemented
        }
        self.running = False

    def run_scraper(self, platform: str):
        """Run a specific scraper and send notifications"""
        if platform not in self.scrapers:
            logger.error(f"Unknown platform: {platform}")
            return

        scraper = self.scrapers[platform]
        logger.info(f"Running {platform} scraper...")

        # Get programs before scraping to track changes
        before_stats = self.db.get_stats()

        # Run scraper
        log = scraper.run()

        # Send notifications
        if log.success and (log.programs_new > 0 or log.programs_updated > 0):
            self.notifier.send_batch_summary(
                log.programs_new,
                log.programs_updated,
                platform
            )

            # Optionally send individual notifications for new programs
            # (Only if there aren't too many to avoid spam)
            if log.programs_new > 0 and log.programs_new <= 5:
                # Get the new programs
                filters = {'platform': platform, 'new_only': True}
                new_programs = self.db.get_all_programs(filters)

                for program_dict in new_programs[:5]:  # Max 5
                    from db.models import Program
                    # Convert dict to Program object (simplified)
                    # In a real scenario, you'd want a proper deserialization method
                    logger.info(f"New program: {program_dict['name']}")
                    # notifier.send_new_program(program) - requires full Program object

        return log

    def run_all_scrapers(self):
        """Run all configured scrapers"""
        logger.info("Running all scrapers")
        for platform in self.scrapers:
            self.run_scraper(platform)
        logger.info("All scrapers complete")

    def start_background_loop(self):
        """Start the background scraping loop"""
        self.running = True

        def loop():
            logger.info(f"Starting background loop (interval: {SCRAPE_INTERVAL_MINUTES} minutes)")

            # Run immediately on startup
            self.run_all_scrapers()

            while self.running:
                time.sleep(SCRAPE_INTERVAL_MINUTES * 60)
                if self.running:  # Check again after sleep
                    self.run_all_scrapers()

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        logger.info("Background loop started")

    def stop(self):
        """Stop the background loop"""
        self.running = False
        logger.info("Stopping scheduler")


def main():
    """Run scheduler as standalone script"""
    scheduler = BountyPingScheduler()

    try:
        scheduler.start_background_loop()

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        scheduler.stop()


if __name__ == '__main__':
    main()
