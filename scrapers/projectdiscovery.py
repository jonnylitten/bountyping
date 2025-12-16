"""
Seed scraper using ProjectDiscovery's chaos-bugbounty-list.json

This is a quick way to seed the database with hundreds of programs
from multiple platforms. Then we can layer live scrapers on top.

Source: https://github.com/projectdiscovery/public-bugbounty-programs
"""

import logging
import re
from typing import List
from urllib.parse import urlparse

from .base import BaseScraper
from db.models import Program
from config import PROJECTDISCOVERY_JSON_URL

logger = logging.getLogger(__name__)


class ProjectDiscoveryScraper(BaseScraper):
    """Seed database using ProjectDiscovery's public bug bounty list"""

    def get_platform_name(self) -> str:
        return "projectdiscovery"

    def scrape_programs(self) -> List[Program]:
        """
        Fetch and parse the chaos-bugbounty-list.json from GitHub.
        Returns programs from all platforms.
        """
        logger.info(f"Fetching ProjectDiscovery list from {PROJECTDISCOVERY_JSON_URL}")

        try:
            data = self.fetch_json(PROJECTDISCOVERY_JSON_URL)
            programs_data = data.get('programs', [])

            logger.info(f"Found {len(programs_data)} programs in ProjectDiscovery list")

            programs = []
            for item in programs_data:
                program = self._parse_program(item)
                if program:
                    programs.append(program)

            return programs

        except Exception as e:
            logger.error(f"Error fetching ProjectDiscovery list: {e}")
            return []

    def _parse_program(self, item: dict) -> Program:
        """Parse a ProjectDiscovery entry into a Program object"""

        # Extract platform from URL
        url = item.get('url', '')
        platform = self._detect_platform(url)

        # Generate slug from URL or name
        slug = self._generate_slug(url, item.get('name', ''))

        # Parse bounty info if available
        bounty_min = None
        bounty_max = None
        vdp_only = False

        bounty = item.get('bounty', '').lower()
        if 'yes' in bounty or '$' in bounty:
            vdp_only = False
            # Try to extract amounts
            amounts = re.findall(r'\$(\d+(?:,\d+)*)', bounty)
            if amounts:
                amounts = [int(a.replace(',', '')) for a in amounts]
                if len(amounts) >= 2:
                    bounty_min = min(amounts)
                    bounty_max = max(amounts)
                elif len(amounts) == 1:
                    bounty_max = amounts[0]
        elif 'no' in bounty or 'swag' in bounty:
            vdp_only = True

        # Parse domains
        domains = item.get('domains', [])

        program = Program(
            id="",  # Auto-generated
            platform=platform,
            name=item.get('name', slug),
            slug=slug,
            url=url,
            bounty_min=bounty_min,
            bounty_max=bounty_max,
            assets=domains[:20] if domains else [],  # Limit to first 20
            asset_types=self._detect_asset_types(domains),
            vdp_only=vdp_only,
            offers_bounties=not vdp_only,
            raw_data=item
        )

        return program

    def _detect_platform(self, url: str) -> str:
        """Detect platform from program URL"""
        if not url:
            return "unknown"

        domain = urlparse(url).netloc.lower()

        if 'hackerone.com' in domain:
            return 'hackerone'
        elif 'bugcrowd.com' in domain:
            return 'bugcrowd'
        elif 'intigriti.com' in domain:
            return 'intigriti'
        elif 'yeswehack.com' in domain:
            return 'yeswehack'
        elif 'immunefi.com' in domain:
            return 'immunefi'
        elif 'code4rena.com' in domain:
            return 'code4rena'
        elif 'huntr.dev' in domain or 'huntr.com' in domain:
            return 'huntr'
        elif 'algora.io' in domain:
            return 'algora'
        else:
            return 'other'

    def _generate_slug(self, url: str, name: str) -> str:
        """Generate a slug from URL or name"""
        if not url:
            # Use name
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            return slug

        # Extract from URL path
        path = urlparse(url).path.strip('/')
        parts = path.split('/')

        # For HackerOne: hackerone.com/company -> company
        # For Bugcrowd: bugcrowd.com/company -> company
        # For others: use last path segment or domain
        if parts:
            slug = parts[-1]
        else:
            slug = urlparse(url).netloc.replace('.', '-')

        slug = re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')
        return slug or 'unknown'

    def _detect_asset_types(self, domains: list) -> list:
        """Detect asset types from domains"""
        types = set()

        for domain in domains[:10]:  # Check first 10
            domain_lower = domain.lower()

            # API endpoints
            if 'api.' in domain_lower or '/api' in domain_lower:
                types.add('api')

            # Mobile apps (sometimes listed as packageName)
            if any(x in domain_lower for x in ['android', 'ios', 'mobile', 'app']):
                types.add('mobile')

            # Default to web
            if domain.startswith('http') or '.' in domain:
                types.add('web')

        return list(types) if types else ['web']
