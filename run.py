#!/usr/bin/env python3
"""
BountyPing - Main runner

Starts both the web app and the background scheduler.
"""

import logging
import sys
from threading import Thread

from config import FLASK_HOST, FLASK_PORT
from scheduler import BountyPingScheduler
from web.app import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start BountyPing server with web app and scheduler"""

    # Start scheduler in background
    scheduler = BountyPingScheduler()
    scheduler.start_background_loop()

    # Start Flask app (blocking)
    logger.info(f"Starting BountyPing web app on {FLASK_HOST}:{FLASK_PORT}")
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
