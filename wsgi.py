#!/usr/bin/env python
import sys
import os

# Add RAG-assistance to path so we can import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RAG-assistance'))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
