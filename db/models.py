"""
Database models for BountyPing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Program:
    """Bug bounty program model"""

    # Core identification
    id: str  # unique hash of platform + program name
    platform: str  # hackerone, bugcrowd, immunefi, etc.
    name: str
    slug: str
    url: str

    # Bounty information
    bounty_min: Optional[int] = None
    bounty_max: Optional[int] = None
    currency: str = "USD"

    # Program details
    assets: list[str] = field(default_factory=list)  # domains, repos, etc.
    asset_types: list[str] = field(default_factory=list)  # web, mobile, api, smart-contract, etc.
    managed: bool = False  # is it a managed/triaged program
    vdp_only: bool = False  # vulnerability disclosure only, no bounty

    # Scope & status
    accepts_submissions: bool = True
    offers_bounties: bool = True

    # Metadata
    first_seen: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    last_scraped: Optional[datetime] = None

    # Raw data storage
    raw_data: Optional[dict] = None  # store original JSON for future parsing

    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id:
            # Create deterministic ID from platform + slug
            import hashlib
            key = f"{self.platform}:{self.slug}".lower()
            self.id = hashlib.md5(key.encode()).hexdigest()[:16]

    @property
    def bounty_range(self) -> str:
        """Human-readable bounty range"""
        if not self.offers_bounties or self.vdp_only:
            return "No bounty (VDP)"

        if self.bounty_min and self.bounty_max:
            return f"${self.bounty_min:,} - ${self.bounty_max:,}"
        elif self.bounty_max:
            return f"Up to ${self.bounty_max:,}"
        elif self.bounty_min:
            return f"From ${self.bounty_min:,}"
        else:
            return "Bounty available"

    @property
    def is_new(self) -> bool:
        """Was this program first seen in the last 7 days?"""
        if not self.first_seen:
            return False

        from datetime import timedelta
        return (datetime.utcnow() - self.first_seen) < timedelta(days=7)


@dataclass
class ScrapeLog:
    """Log entry for scraping operations"""
    id: Optional[int] = None
    platform: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    programs_found: int = 0
    programs_new: int = 0
    programs_updated: int = 0
    success: bool = True
    error_message: Optional[str] = None
