"""
Base scraper class for all bug bounty platforms
"""

import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

import requests

from config import USER_AGENT, REQUEST_DELAY
from db.models import Program, ScrapeLog
from db.database import BountyDatabase

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for platform scrapers"""

    def __init__(self, db: BountyDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.platform_name = self.get_platform_name()

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform identifier (e.g., 'hackerone', 'bugcrowd')"""
        pass

    @abstractmethod
    def scrape_programs(self) -> List[Program]:
        """
        Scrape all public programs from the platform.
        Returns a list of Program objects.
        """
        pass

    def run(self) -> ScrapeLog:
        """
        Execute the scraper and update database.
        Returns a ScrapeLog with results.
        """
        log = ScrapeLog(
            platform=self.platform_name,
            started_at=datetime.utcnow()
        )

        try:
            logger.info(f"Starting scrape for {self.platform_name}")
            programs = self.scrape_programs()
            log.programs_found = len(programs)

            new_count = 0
            updated_count = 0

            for program in programs:
                is_new, is_updated = self.db.upsert_program(program)
                if is_new:
                    new_count += 1
                    logger.info(f"New program: {program.name}")
                elif is_updated:
                    updated_count += 1
                    logger.info(f"Updated program: {program.name}")

            log.programs_new = new_count
            log.programs_updated = updated_count
            log.success = True
            log.completed_at = datetime.utcnow()

            logger.info(
                f"Scrape complete for {self.platform_name}: "
                f"{log.programs_found} found, {new_count} new, {updated_count} updated"
            )

        except Exception as e:
            log.success = False
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            logger.error(f"Scrape failed for {self.platform_name}: {e}", exc_info=True)

        # Log to database
        self.db.log_scrape(log)
        return log

    def fetch(self, url: str, **kwargs) -> requests.Response:
        """
        Fetch a URL with polite delays.
        """
        time.sleep(REQUEST_DELAY)
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def fetch_json(self, url: str, **kwargs) -> dict:
        """Fetch JSON endpoint"""
        response = self.fetch(url, **kwargs)
        return response.json()
