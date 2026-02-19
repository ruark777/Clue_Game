#!/usr/bin/env python3
"""
Main entry point for Clue Game Web Application
"""

import sys
import os

# Add the src directory to Python path for game logic
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import and run the web app
from web_app import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
