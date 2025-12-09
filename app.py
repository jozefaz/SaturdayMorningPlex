#!/usr/bin/env python3
"""
SaturdayMorningPlex - Automated playlist generator for Plex
Creates Saturday morning cartoon-style weekly playlists
"""
from flask import Flask, render_template, jsonify, request
import os
import logging
from datetime import datetime
from plex_connection import PlexConnection
from playlist_generator import PlaylistGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
APP_PORT = int(os.getenv('APP_PORT', 5000))
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')

# Plex configuration
PLEX_URL = os.getenv('PLEX_URL', '')
PLEX_TOKEN = os.getenv('PLEX_TOKEN', '')
PLEX_USERNAME = os.getenv('PLEX_USERNAME', '')
PLEX_PASSWORD = os.getenv('PLEX_PASSWORD', '')
PLEX_SERVER_NAME = os.getenv('PLEX_SERVER_NAME', '')
TV_LIBRARY_NAME = os.getenv('TV_LIBRARY_NAME', 'TV Shows')
CONTENT_RATINGS = os.getenv('CONTENT_RATINGS', 'G,PG').split(',')
CONTENT_RATINGS = [rating.strip() for rating in CONTENT_RATINGS if rating.strip()]

# Global Plex connection (will be initialized on first use)
plex_conn = None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         app_name="SaturdayMorningPlex",
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         plex_configured=bool(PLEX_URL and PLEX_TOKEN) or bool(PLEX_USERNAME and PLEX_PASSWORD),
                         content_ratings=','.join(CONTENT_RATINGS),
                         tv_library=TV_LIBRARY_NAME)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'app': 'SaturdayMorningPlex',
        'plex_configured': bool(PLEX_URL and PLEX_TOKEN) or bool(PLEX_USERNAME and PLEX_PASSWORD)
    })

@app.route('/api/info')
def info():
    """Application info endpoint"""
    return jsonify({
        'name': 'SaturdayMorningPlex',
        'version': '2.0.0',
        'description': 'Automated Plex playlist generator for Saturday morning cartoons',
        'environment': {
            'port': APP_PORT,
            'host': APP_HOST,
            'plex_configured': bool(PLEX_URL and PLEX_TOKEN) or bool(PLEX_USERNAME and PLEX_PASSWORD),
            'tv_library': TV_LIBRARY_NAME,
            'content_ratings': CONTENT_RATINGS
        }
    })

@app.route('/api/plex/test', methods=['POST'])
def test_plex_connection():
    """Test Plex connection with provided or stored credentials"""
    try:
        data = request.get_json() or {}
        
        # Use provided credentials or fall back to environment variables
        url = data.get('plex_url', PLEX_URL)
        token = data.get('plex_token', PLEX_TOKEN)
        username = data.get('plex_username', PLEX_USERNAME)
        password = data.get('plex_password', PLEX_PASSWORD)
        servername = data.get('plex_servername', PLEX_SERVER_NAME)
        
        # Create connection
        conn = PlexConnection(
            baseurl=url if url else None,
            token=token if token else None,
            username=username if username else None,
            password=password if password else None,
            servername=servername if servername else None
        )
        
        result = conn.test_connection()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Plex connection test failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/plex/libraries')
def get_plex_libraries():
    """Get available Plex library sections"""
    try:
        global plex_conn
        if not plex_conn:
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        sections = plex_conn.plex.library.sections()
        return jsonify({
            'success': True,
            'libraries': [
                {
                    'title': s.title,
                    'type': s.type,
                    'key': s.key
                }
                for s in sections
            ]
        })
    except Exception as e:
        logger.error(f"Failed to get libraries: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/plex/content-ratings')
def get_content_ratings():
    """Get available content ratings from TV library"""
    try:
        global plex_conn
        if not plex_conn:
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        tv_section = plex_conn.get_tv_section(TV_LIBRARY_NAME)
        
        # Get all unique content ratings
        ratings = set()
        for show in tv_section.all():
            if show.contentRating:
                ratings.add(show.contentRating)
        
        return jsonify({
            'success': True,
            'ratings': sorted(list(ratings))
        })
    except Exception as e:
        logger.error(f"Failed to get content ratings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/playlists/generate', methods=['POST'])
def generate_playlists():
    """Generate Saturday Morning playlists"""
    try:
        data = request.get_json() or {}
        
        # Get parameters
        content_ratings = data.get('content_ratings', CONTENT_RATINGS)
        if isinstance(content_ratings, str):
            content_ratings = [r.strip() for r in content_ratings.split(',') if r.strip()]
        
        tv_library = data.get('tv_library', TV_LIBRARY_NAME)
        playlist_prefix = data.get('playlist_prefix', 'Saturday Morning')
        weeks_per_year = int(data.get('weeks_per_year', 52))
        
        # Initialize connection if needed
        global plex_conn
        if not plex_conn:
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        # Generate playlists
        generator = PlaylistGenerator(plex_conn)
        result = generator.generate_all_playlists(
            tv_section_name=tv_library,
            content_ratings=content_ratings,
            playlist_prefix=playlist_prefix,
            weeks_per_year=weeks_per_year
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to generate playlists: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/playlists/summary')
def get_playlists_summary():
    """Get summary of existing playlists"""
    try:
        playlist_prefix = request.args.get('prefix', 'Saturday Morning')
        
        global plex_conn
        if not plex_conn:
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        generator = PlaylistGenerator(plex_conn)
        result = generator.get_playlist_summary(playlist_prefix)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to get playlist summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/playlists/delete', methods=['POST'])
def delete_playlists():
    """Delete all Saturday Morning playlists"""
    try:
        data = request.get_json() or {}
        playlist_prefix = data.get('playlist_prefix', 'Saturday Morning')
        
        global plex_conn
        if not plex_conn:
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        generator = PlaylistGenerator(plex_conn)
        result = generator.delete_all_playlists(playlist_prefix)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to delete playlists: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info(f"Starting SaturdayMorningPlex on {APP_HOST}:{APP_PORT}")
    app.run(host=APP_HOST, port=APP_PORT, debug=False)
