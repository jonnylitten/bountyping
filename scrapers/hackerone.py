"""
HackerOne public programs scraper

HackerOne has a GraphQL API for their directory that we can use.
Endpoint: https://hackerone.com/graphql
"""

import logging
from typing import List

from .base import BaseScraper
from db.models import Program

logger = logging.getLogger(__name__)


class HackerOneScraper(BaseScraper):
    """Scraper for HackerOne public bug bounty programs"""

    GRAPHQL_URL = "https://hackerone.com/graphql"

    def get_platform_name(self) -> str:
        return "hackerone"

    def scrape_programs(self) -> List[Program]:
        """
        Scrape all public programs from HackerOne directory using GraphQL API.
        """
        programs = []
        cursor = None
        page = 1

        while True:
            logger.info(f"Fetching HackerOne page {page}")

            # GraphQL query for directory (simplified - HackerOne changed their schema)
            query = """
            query DirectoryQuery($cursor: String) {
              teams(
                first: 100
                after: $cursor
                secure_order_by: {started_accepting_at: {_direction: DESC}}
                where: {
                  state: {_eq: public_mode}
                }
              ) {
                pageInfo {
                  endCursor
                  hasNextPage
                }
                edges {
                  node {
                    id
                    handle
                    name
                    currency
                    state
                    submission_state
                    offers_bounties
                    offers_swag
                    base_bounty
                    url
                    started_accepting_at
                  }
                }
              }
            }
            """

            variables = {"cursor": cursor} if cursor else {}

            try:
                response = self.session.post(
                    self.GRAPHQL_URL,
                    json={"query": query, "variables": variables},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                if 'errors' in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    break

                teams_data = data.get('data', {}).get('teams', {})
                edges = teams_data.get('edges', [])
                page_info = teams_data.get('pageInfo', {})

                if not edges:
                    break

                # Parse each program
                for edge in edges:
                    node = edge['node']
                    program = self._parse_program(node)
                    if program:
                        programs.append(program)

                # Check if there are more pages
                if not page_info.get('hasNextPage'):
                    break

                cursor = page_info.get('endCursor')
                page += 1

            except Exception as e:
                logger.error(f"Error fetching HackerOne page {page}: {e}")
                break

        logger.info(f"Scraped {len(programs)} programs from HackerOne")
        return programs

    def _parse_program(self, node: dict) -> Program:
        """Parse a HackerOne program node into a Program object"""
        handle = node.get('handle', '')
        name = node.get('name', handle)

        # Determine if VDP only
        offers_bounties = node.get('offers_bounties', False)
        submission_state = node.get('submission_state', '')
        vdp_only = not offers_bounties

        # Parse bounty amounts (base_bounty is a minimum)
        base_bounty = node.get('base_bounty')
        bounty_min = None
        bounty_max = None

        if base_bounty and offers_bounties:
            bounty_min = int(base_bounty)
            # HackerOne doesn't expose max in directory, we'd need to scrape individual pages

        # Build program URL
        url = f"https://hackerone.com/{handle}"

        program = Program(
            id="",  # Will be auto-generated in __post_init__
            platform="hackerone",
            name=name,
            slug=handle,
            url=url,
            bounty_min=bounty_min,
            bounty_max=bounty_max,
            currency=node.get('currency', 'USD'),
            assets=[],  # Would need individual page scraping
            asset_types=[],  # Would need individual page scraping
            managed=False,  # Can't determine from directory
            vdp_only=vdp_only,
            accepts_submissions=(submission_state == 'open'),
            offers_bounties=offers_bounties,
            raw_data=node
        )

        return program
