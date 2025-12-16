"""
SQLite database operations for BountyPing
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Program, ScrapeLog


class BountyDatabase:
    """Handles all database operations"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Programs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                url TEXT NOT NULL,

                bounty_min INTEGER,
                bounty_max INTEGER,
                currency TEXT DEFAULT 'USD',

                assets TEXT DEFAULT '[]',
                asset_types TEXT DEFAULT '[]',
                managed INTEGER DEFAULT 0,
                vdp_only INTEGER DEFAULT 0,

                accepts_submissions INTEGER DEFAULT 1,
                offers_bounties INTEGER DEFAULT 1,

                first_seen TEXT,
                last_updated TEXT,
                last_scraped TEXT,

                raw_data TEXT,

                UNIQUE(platform, slug)
            )
        """)

        # Scrape logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                programs_found INTEGER DEFAULT 0,
                programs_new INTEGER DEFAULT 0,
                programs_updated INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1,
                error_message TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform ON programs(platform)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_first_seen ON programs(first_seen)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bounty_max ON programs(bounty_max)")

        conn.commit()
        conn.close()

    def upsert_program(self, program: Program) -> tuple[bool, bool]:
        """
        Insert or update a program.
        Returns (is_new, is_updated)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        # Check if program exists
        cursor.execute("SELECT * FROM programs WHERE id = ?", (program.id,))
        existing = cursor.fetchone()

        is_new = existing is None
        is_updated = False

        if is_new:
            # New program
            program.first_seen = datetime.utcnow()
            program.last_updated = datetime.utcnow()
            program.last_scraped = datetime.utcnow()

            cursor.execute("""
                INSERT INTO programs (
                    id, platform, name, slug, url,
                    bounty_min, bounty_max, currency,
                    assets, asset_types, managed, vdp_only,
                    accepts_submissions, offers_bounties,
                    first_seen, last_updated, last_scraped,
                    raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                program.id, program.platform, program.name, program.slug, program.url,
                program.bounty_min, program.bounty_max, program.currency,
                json.dumps(program.assets), json.dumps(program.asset_types),
                int(program.managed), int(program.vdp_only),
                int(program.accepts_submissions), int(program.offers_bounties),
                program.first_seen.isoformat() if program.first_seen else now,
                program.last_updated.isoformat() if program.last_updated else now,
                program.last_scraped.isoformat() if program.last_scraped else now,
                json.dumps(program.raw_data) if program.raw_data else None
            ))

        else:
            # Existing program - check if anything changed
            old_data = {
                'bounty_min': existing['bounty_min'],
                'bounty_max': existing['bounty_max'],
                'assets': existing['assets'],
                'url': existing['url']
            }

            new_data = {
                'bounty_min': program.bounty_min,
                'bounty_max': program.bounty_max,
                'assets': json.dumps(program.assets),
                'url': program.url
            }

            is_updated = old_data != new_data

            # Update with latest data
            cursor.execute("""
                UPDATE programs SET
                    name = ?,
                    url = ?,
                    bounty_min = ?,
                    bounty_max = ?,
                    currency = ?,
                    assets = ?,
                    asset_types = ?,
                    managed = ?,
                    vdp_only = ?,
                    accepts_submissions = ?,
                    offers_bounties = ?,
                    last_updated = ?,
                    last_scraped = ?,
                    raw_data = ?
                WHERE id = ?
            """, (
                program.name,
                program.url,
                program.bounty_min,
                program.bounty_max,
                program.currency,
                json.dumps(program.assets),
                json.dumps(program.asset_types),
                int(program.managed),
                int(program.vdp_only),
                int(program.accepts_submissions),
                int(program.offers_bounties),
                now if is_updated else existing['last_updated'],
                now,
                json.dumps(program.raw_data) if program.raw_data else None,
                program.id
            ))

        conn.commit()
        conn.close()

        return is_new, is_updated

    def get_all_programs(self, filters: Optional[dict] = None) -> list[dict]:
        """Get all programs with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM programs WHERE 1=1"
        params = []

        if filters:
            if platform := filters.get('platform'):
                query += " AND platform = ?"
                params.append(platform)

            if min_bounty := filters.get('min_bounty'):
                query += " AND bounty_max >= ?"
                params.append(min_bounty)

            if asset_type := filters.get('asset_type'):
                query += " AND asset_types LIKE ?"
                params.append(f'%{asset_type}%')

            if search := filters.get('search'):
                query += " AND (name LIKE ? OR slug LIKE ?)"
                params.extend([f'%{search}%', f'%{search}%'])

            if filters.get('new_only'):
                query += " AND datetime(first_seen) >= datetime('now', '-7 days')"

            if filters.get('bounties_only'):
                query += " AND vdp_only = 0 AND offers_bounties = 1"

        # Default sort by newest first
        sort_by = filters.get('sort_by', 'newest') if filters else 'newest'
        if sort_by == 'newest':
            query += " ORDER BY first_seen DESC"
        elif sort_by == 'bounty':
            query += " ORDER BY bounty_max DESC NULLS LAST"
        elif sort_by == 'name':
            query += " ORDER BY name ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        programs = []
        for row in rows:
            program_dict = dict(row)
            # Parse JSON fields
            program_dict['assets'] = json.loads(program_dict.get('assets', '[]'))
            program_dict['asset_types'] = json.loads(program_dict.get('asset_types', '[]'))
            program_dict['raw_data'] = json.loads(program_dict['raw_data']) if program_dict.get('raw_data') else None
            programs.append(program_dict)

        conn.close()
        return programs

    def get_stats(self) -> dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM programs")
        total = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as new FROM programs WHERE datetime(first_seen) >= datetime('now', '-7 days')")
        new_this_week = cursor.fetchone()['new']

        cursor.execute("SELECT COUNT(*) as paid FROM programs WHERE vdp_only = 0 AND offers_bounties = 1")
        paid_programs = cursor.fetchone()['paid']

        cursor.execute("SELECT COUNT(DISTINCT platform) as platforms FROM programs")
        platforms = cursor.fetchone()['platforms']

        cursor.execute("SELECT platform, COUNT(*) as count FROM programs GROUP BY platform ORDER BY count DESC")
        by_platform = {row['platform']: row['count'] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_programs': total,
            'new_this_week': new_this_week,
            'paid_programs': paid_programs,
            'platforms': platforms,
            'by_platform': by_platform
        }

    def log_scrape(self, log: ScrapeLog):
        """Log a scraping operation"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scrape_logs (
                platform, started_at, completed_at,
                programs_found, programs_new, programs_updated,
                success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log.platform,
            log.started_at.isoformat() if log.started_at else None,
            log.completed_at.isoformat() if log.completed_at else None,
            log.programs_found,
            log.programs_new,
            log.programs_updated,
            int(log.success),
            log.error_message
        ))

        conn.commit()
        conn.close()

    def get_recent_logs(self, limit: int = 20) -> list[dict]:
        """Get recent scrape logs"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM scrape_logs
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))

        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
