#!/usr/bin/env python3
"""
BountyPing CLI

Command-line interface for managing BountyPing.
"""

import argparse
import logging
import sys

from config import DB_PATH
from db.database import BountyDatabase
from scrapers.hackerone import HackerOneScraper
from scrapers.projectdiscovery import ProjectDiscoveryScraper
from notifiers.discord import DiscordNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_seed(args):
    """Seed database with ProjectDiscovery data"""
    db = BountyDatabase(args.db)
    scraper = ProjectDiscoveryScraper(db)

    logger.info("Seeding database with ProjectDiscovery data...")
    log = scraper.run()

    if log.success:
        print(f"\n✅ Seed complete!")
        print(f"  Found: {log.programs_found}")
        print(f"  New: {log.programs_new}")
        print(f"  Updated: {log.programs_updated}")
    else:
        print(f"\n❌ Seed failed: {log.error_message}")
        sys.exit(1)


def cmd_scrape(args):
    """Run scraper for a specific platform"""
    db = BountyDatabase(args.db)

    scrapers = {
        'hackerone': HackerOneScraper,
        'projectdiscovery': ProjectDiscoveryScraper,
    }

    platform = args.platform.lower()
    if platform not in scrapers:
        print(f"❌ Unknown platform: {platform}")
        print(f"Available platforms: {', '.join(scrapers.keys())}")
        sys.exit(1)

    scraper = scrapers[platform](db)
    logger.info(f"Scraping {platform}...")

    log = scraper.run()

    if log.success:
        print(f"\n✅ Scrape complete!")
        print(f"  Found: {log.programs_found}")
        print(f"  New: {log.programs_new}")
        print(f"  Updated: {log.programs_updated}")

        # Send notification if configured
        if args.notify and (log.programs_new > 0 or log.programs_updated > 0):
            notifier = DiscordNotifier()
            notifier.send_batch_summary(log.programs_new, log.programs_updated, platform)
    else:
        print(f"\n❌ Scrape failed: {log.error_message}")
        sys.exit(1)


def cmd_stats(args):
    """Show database statistics"""
    db = BountyDatabase(args.db)
    stats = db.get_stats()

    print("\n📊 BountyPing Statistics")
    print("=" * 40)
    print(f"Total programs:    {stats['total_programs']:,}")
    print(f"New this week:     {stats['new_this_week']:,}")
    print(f"Paid programs:     {stats['paid_programs']:,}")
    print(f"Platforms:         {stats['platforms']}")
    print("\nBy platform:")
    for platform, count in sorted(stats['by_platform'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {platform:20s} {count:,}")


def cmd_search(args):
    """Search programs"""
    db = BountyDatabase(args.db)

    filters = {}
    if args.platform:
        filters['platform'] = args.platform
    if args.min_bounty:
        filters['min_bounty'] = args.min_bounty
    if args.search:
        filters['search'] = args.search
    if args.bounties_only:
        filters['bounties_only'] = True

    programs = db.get_all_programs(filters)

    print(f"\n🔍 Found {len(programs)} program(s)")
    print("=" * 80)

    for p in programs[:args.limit]:
        bounty = "VDP" if p.get('vdp_only') else (
            f"${p.get('bounty_min', 0):,}-${p.get('bounty_max', 0):,}" if p.get('bounty_max') else "Bounty available"
        )

        print(f"\n{p['name']}")
        print(f"  Platform: {p['platform']} | Bounty: {bounty}")
        print(f"  URL: {p['url']}")


def cmd_logs(args):
    """Show recent scrape logs"""
    db = BountyDatabase(args.db)
    logs = db.get_recent_logs(limit=args.limit)

    print(f"\n📝 Recent scrape logs ({len(logs)})")
    print("=" * 80)

    for log in logs:
        status = "✅" if log['success'] else "❌"
        print(f"\n{status} {log['platform']} - {log['started_at']}")
        print(f"   Found: {log['programs_found']} | New: {log['programs_new']} | Updated: {log['programs_updated']}")
        if log['error_message']:
            print(f"   Error: {log['error_message']}")


def main():
    parser = argparse.ArgumentParser(description='BountyPing CLI')
    parser.add_argument('--db', default=DB_PATH, help='Database path')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Seed command
    seed_parser = subparsers.add_parser('seed', help='Seed database with ProjectDiscovery data')

    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape a platform')
    scrape_parser.add_argument('platform', help='Platform to scrape (hackerone, projectdiscovery, etc.)')
    scrape_parser.add_argument('--notify', action='store_true', help='Send Discord notification')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search programs')
    search_parser.add_argument('--platform', help='Filter by platform')
    search_parser.add_argument('--min-bounty', type=int, help='Minimum bounty amount')
    search_parser.add_argument('--search', help='Search term')
    search_parser.add_argument('--bounties-only', action='store_true', help='Only paid programs')
    search_parser.add_argument('--limit', type=int, default=20, help='Max results')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show recent scrape logs')
    logs_parser.add_argument('--limit', type=int, default=20, help='Number of logs to show')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        'seed': cmd_seed,
        'scrape': cmd_scrape,
        'stats': cmd_stats,
        'search': cmd_search,
        'logs': cmd_logs,
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
