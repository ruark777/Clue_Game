#!/usr/bin/env python3
"""
Local test entry point for Clue Game Web Application
Optimized for fast local testing and development iterations
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the web app
from web.web_app import app

if __name__ == '__main__':
    # Local development configuration
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=True)
