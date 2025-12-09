#!/usr/bin/env python3
"""
SaturdayMorningPlex - A simple web application for UnRAID
"""
from flask import Flask, render_template, jsonify
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
APP_PORT = int(os.getenv('APP_PORT', 5000))
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         app_name="SaturdayMorningPlex",
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'app': 'SaturdayMorningPlex'
    })

@app.route('/api/info')
def info():
    """Application info endpoint"""
    return jsonify({
        'name': 'SaturdayMorningPlex',
        'version': '1.0.0',
        'description': 'Container application for UnRAID',
        'environment': {
            'port': APP_PORT,
            'host': APP_HOST
        }
    })

if __name__ == '__main__':
    logger.info(f"Starting SaturdayMorningPlex on {APP_HOST}:{APP_PORT}")
    app.run(host=APP_HOST, port=APP_PORT, debug=False)
