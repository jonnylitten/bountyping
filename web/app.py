"""
BountyPing Flask Web App

Simple web interface for browsing and filtering bug bounty programs.
"""

import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from config import FLASK_HOST, FLASK_PORT, SECRET_KEY, DB_PATH, ADMIN_SECRET
from db.database import BountyDatabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)

# Initialize database
db = BountyDatabase(DB_PATH)


@app.route('/')
def index():
    """Main page - show all programs with filters"""
    return render_template('index.html')


@app.route('/api/programs')
def get_programs():
    """
    API endpoint to get programs with filters.

    Query params:
    - platform: Filter by platform (hackerone, bugcrowd, etc.)
    - min_bounty: Minimum bounty amount
    - asset_type: Filter by asset type (web, mobile, api, etc.)
    - search: Search in name/slug
    - sort_by: Sort order (newest, bounty, name)
    - new_only: Only show programs from last 7 days (true/false)
    - bounties_only: Only show paid programs (true/false)
    """
    filters = {}

    if platform := request.args.get('platform'):
        filters['platform'] = platform

    if min_bounty := request.args.get('min_bounty'):
        try:
            filters['min_bounty'] = int(min_bounty)
        except ValueError:
            pass

    if asset_type := request.args.get('asset_type'):
        filters['asset_type'] = asset_type

    if search := request.args.get('search'):
        filters['search'] = search

    if sort_by := request.args.get('sort_by'):
        filters['sort_by'] = sort_by

    if request.args.get('new_only') == 'true':
        filters['new_only'] = True

    if request.args.get('bounties_only') == 'true':
        filters['bounties_only'] = True

    programs = db.get_all_programs(filters)

    return jsonify({
        'programs': programs,
        'count': len(programs)
    })


@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    stats = db.get_stats()
    return jsonify(stats)


@app.route('/api/platforms')
def get_platforms():
    """Get list of all platforms with program counts"""
    stats = db.get_stats()
    platforms = [
        {'name': platform, 'count': count}
        for platform, count in stats['by_platform'].items()
    ]
    return jsonify({'platforms': platforms})


@app.route('/api/admin/scrape-logs')
def get_scrape_logs():
    """Get recent scrape logs (admin only)"""
    # Simple admin auth via header
    admin_secret = request.headers.get('X-Admin-Secret')
    if admin_secret != ADMIN_SECRET or not ADMIN_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    logs = db.get_recent_logs(limit=50)
    return jsonify({'logs': logs})


@app.route('/health')
def health():
    """Health check endpoint"""
    stats = db.get_stats()
    return jsonify({
        'status': 'ok',
        'total_programs': stats['total_programs']
    })


if __name__ == '__main__':
    logger.info(f"Starting BountyPing web app on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
