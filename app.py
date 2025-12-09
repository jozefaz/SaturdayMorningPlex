#!/usr/bin/env python3
"""
SaturdayMorningPlex - Automated playlist generator for Plex
Creates Saturday morning cartoon-style weekly playlists
"""
from flask import Flask, render_template, jsonify, request
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from plex_connection import PlexConnection
from playlist_generator import PlaylistGenerator

# Configure logging for Docker and UnRAID compatibility
def setup_logging():
    """
    Configure logging to output to both stdout (Docker logs) and file (UnRAID logs).
    - Docker: Logs to stdout/stderr (viewable via 'docker logs')
    - UnRAID: Logs to /config/logs/saturdaymorningplex.log (persistent)
    - Formats: ISO8601 timestamps, structured logging
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Console handler (stdout) - for Docker logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - for UnRAID persistent logs
    log_dir = os.getenv('LOG_DIR', '/config/logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            # If can't create log directory, log to /tmp as fallback
            log_dir = '/tmp'
            root_logger.warning(f"Could not create log directory, using {log_dir}: {e}")
    
    log_file = os.path.join(log_dir, 'saturdaymorningplex.log')
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        root_logger.info(f"File logging enabled: {log_file}")
    except (OSError, PermissionError) as e:
        root_logger.warning(f"Could not create log file {log_file}: {e}")
    
    # Log startup information
    root_logger.info("="*60)
    root_logger.info("SaturdayMorningPlex Starting")
    root_logger.info(f"Log Level: {log_level}")
    root_logger.info(f"Python Version: {sys.version}")
    root_logger.info(f"Log Directory: {log_dir}")
    root_logger.info("="*60)

setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Suppress Flask's default logging to avoid duplicate entries
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

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

logger.debug(f"Environment: PLEX_URL={'set' if PLEX_URL else 'not set'}, "
             f"PLEX_TOKEN={'set' if PLEX_TOKEN else 'not set'}, "
             f"TV_LIBRARY={TV_LIBRARY_NAME}, "
             f"CONTENT_RATINGS={CONTENT_RATINGS}")

@app.route('/')
def index():
    """Main page"""
    logger.info("Web interface accessed")
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
    logger.info("Testing Plex connection")
    try:
        data = request.get_json() or {}
        
        # Use provided credentials or fall back to environment variables
        url = data.get('plex_url', PLEX_URL)
        token = data.get('plex_token', PLEX_TOKEN)
        username = data.get('plex_username', PLEX_USERNAME)
        password = data.get('plex_password', PLEX_PASSWORD)
        servername = data.get('plex_servername', PLEX_SERVER_NAME)
        
        logger.debug(f"Connection method: {'Direct' if (url and token) else 'MyPlex Account'}")
        
        # Create connection
        conn = PlexConnection(
            baseurl=url if url else None,
            token=token if token else None,
            username=username if username else None,
            password=password if password else None,
            servername=servername if servername else None
        )
        
        result = conn.test_connection()
        if result.get('success'):
            logger.info(f"Plex connection successful: {result.get('server_name')}")
        else:
            logger.error(f"Plex connection failed: {result.get('error')}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Plex connection test failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/plex/libraries')
def get_plex_libraries():
    """Get available Plex library sections"""
    logger.info("Fetching Plex library sections")
    try:
        global plex_conn
        if not plex_conn:
            logger.debug("Initializing new Plex connection")
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        sections = plex_conn.plex.library.sections()
        logger.info(f"Found {len(sections)} library sections")
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
        logger.error(f"Failed to get libraries: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/plex/content-ratings')
def get_content_ratings():
    """Get available content ratings from TV library"""
    logger.info("Fetching available content ratings")
    try:
        global plex_conn
        if not plex_conn:
            logger.debug("Initializing new Plex connection")
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        logger.debug(f"Fetching TV section: {TV_LIBRARY_NAME}")
        tv_section = plex_conn.get_tv_section(TV_LIBRARY_NAME)
        
        # Get all unique content ratings
        ratings = set()
        for show in tv_section.all():
            if show.contentRating:
                ratings.add(show.contentRating)
        
        logger.info(f"Found {len(ratings)} unique content ratings")
        
        return jsonify({
            'success': True,
            'ratings': sorted(list(ratings))
        })
    except Exception as e:
        logger.error(f"Failed to get content ratings: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/plex/validate-ratings', methods=['POST'])
def validate_content_ratings():
    """Validate that selected content ratings exist in the library"""
    logger.info("Validating content ratings")
    try:
        data = request.get_json() or {}
        content_ratings = data.get('content_ratings', [])
        if isinstance(content_ratings, str):
            content_ratings = [r.strip() for r in content_ratings.split(',') if r.strip()]
        
        tv_library = data.get('tv_library', TV_LIBRARY_NAME)
        
        global plex_conn
        if not plex_conn:
            logger.debug("Initializing new Plex connection")
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        logger.debug(f"Fetching TV section: {tv_library}")
        tv_section = plex_conn.get_tv_section(tv_library)
        
        # Get all unique content ratings in library
        library_ratings = set()
        for show in tv_section.all():
            if show.contentRating:
                library_ratings.add(show.contentRating)
        
        # Check which selected ratings are missing
        missing_ratings = [r for r in content_ratings if r not in library_ratings]
        
        if missing_ratings:
            logger.warning(f"Selected ratings not found in library: {missing_ratings}")
            return jsonify({
                'success': False,
                'valid': False,
                'missing_ratings': missing_ratings,
                'available_ratings': sorted(list(library_ratings)),
                'error': f"The following content ratings are not found in '{tv_library}': {', '.join(missing_ratings)}"
            })
        
        logger.info(f"All selected ratings are valid: {content_ratings}")
        return jsonify({
            'success': True,
            'valid': True,
            'selected_ratings': content_ratings,
            'available_ratings': sorted(list(library_ratings))
        })
    except Exception as e:
        logger.error(f"Failed to validate content ratings: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/playlists/generate', methods=['POST'])
def generate_playlists():
    """Generate Saturday Morning playlists"""
    logger.info("Playlist generation requested")
    try:
        data = request.get_json() or {}
        
        # Get parameters
        content_ratings = data.get('content_ratings', CONTENT_RATINGS)
        if isinstance(content_ratings, str):
            content_ratings = [r.strip() for r in content_ratings.split(',') if r.strip()]
        
        tv_library = data.get('tv_library', TV_LIBRARY_NAME)
        # Support comma-separated library names
        if isinstance(tv_library, str):
            tv_libraries = [lib.strip() for lib in tv_library.split(',') if lib.strip()]
        else:
            tv_libraries = tv_library if isinstance(tv_library, list) else [tv_library]
        
        playlist_prefix = data.get('playlist_prefix', 'Saturday Morning')
        weeks_per_year = int(data.get('weeks_per_year', 52))
        animation_only = data.get('animation_only', False)
        
        logger.info(f"Generation parameters: libraries={tv_libraries}, ratings={content_ratings}, "
                   f"prefix='{playlist_prefix}', weeks={weeks_per_year}, animation_only={animation_only}")
        
        # Initialize connection if needed
        global plex_conn
        if not plex_conn:
            logger.debug("Initializing new Plex connection")
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        # Validate content ratings exist in library/libraries
        logger.info("Validating content ratings against library...")
        all_library_ratings = set()
        
        for lib_name in tv_libraries:
            try:
                tv_section = plex_conn.get_tv_section(lib_name)
                for show in tv_section.all():
                    if show.contentRating:
                        all_library_ratings.add(show.contentRating)
            except Exception as e:
                logger.error(f"Failed to access library '{lib_name}': {e}")
                return jsonify({
                    'success': False,
                    'error': f"Library '{lib_name}' not found or inaccessible"
                }), 400
        
        missing_ratings = [r for r in content_ratings if r not in all_library_ratings]
        if missing_ratings:
            error_msg = f"Content ratings not found in libraries {tv_libraries}: {', '.join(missing_ratings)}. Available: {', '.join(sorted(all_library_ratings))}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'error': error_msg,
                'missing_ratings': missing_ratings,
                'available_ratings': sorted(list(all_library_ratings))
            }), 400
        
        logger.info("Content ratings validated successfully")
        
        # Continue with existing connection
        if not plex_conn:
            logger.debug("Initializing new Plex connection")
            plex_conn = PlexConnection(
                baseurl=PLEX_URL if PLEX_URL else None,
                token=PLEX_TOKEN if PLEX_TOKEN else None,
                username=PLEX_USERNAME if PLEX_USERNAME else None,
                password=PLEX_PASSWORD if PLEX_PASSWORD else None,
                servername=PLEX_SERVER_NAME if PLEX_SERVER_NAME else None
            )
            plex_conn.connect()
        
        # Generate playlists
        logger.info("Initializing PlaylistGenerator")
        generator = PlaylistGenerator(plex_conn)
        result = generator.generate_all_playlists(
            tv_section_name=tv_libraries,  # Now supports list of library names
            content_ratings=content_ratings,
            playlist_prefix=playlist_prefix,
            weeks_per_year=weeks_per_year,
            animation_only=animation_only
        )
        
        if result.get('success'):
            logger.info(f"Playlist generation complete: {result.get('playlists_created')} playlists created")
        else:
            logger.error(f"Playlist generation failed: {result.get('error')}")
        
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
    logger.info("Fetching playlist summary")
    try:
        playlist_prefix = request.args.get('prefix', 'Saturday Morning')
        logger.debug(f"Searching for playlists with prefix: {playlist_prefix}")
        
        global plex_conn
        if not plex_conn:
            logger.debug("Initializing new Plex connection")
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
        
        if result.get('success'):
            logger.info(f"Found {result.get('total_playlists', 0)} playlists")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to get playlist summary: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/playlists/delete', methods=['POST'])
def delete_playlists():
    """Delete all Saturday Morning playlists"""
    logger.info("Playlist deletion requested")
    try:
        data = request.get_json() or {}
        playlist_prefix = data.get('playlist_prefix', 'Saturday Morning')
        logger.warning(f"Deleting all playlists with prefix: {playlist_prefix}")
        
        global plex_conn
        if not plex_conn:
            logger.debug("Initializing new Plex connection")
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
        
        if result.get('success'):
            logger.info(f"Deleted {result.get('deleted_count', 0)} playlists")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to delete playlists: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info(f"Starting SaturdayMorningPlex on {APP_HOST}:{APP_PORT}")
    logger.info(f"Plex configured: {bool(PLEX_URL and PLEX_TOKEN) or bool(PLEX_USERNAME and PLEX_PASSWORD)}")
    logger.info(f"TV Library: {TV_LIBRARY_NAME}")
    logger.info(f"Content Ratings: {','.join(CONTENT_RATINGS)}")
    logger.debug("Starting Flask application...")
    app.run(host=APP_HOST, port=APP_PORT, debug=False)
