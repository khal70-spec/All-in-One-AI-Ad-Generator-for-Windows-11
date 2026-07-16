#!/usr/bin/env python3
"""
Alternative launcher for the AI Ad Generator (app.py).

This simply delegates to main.py's entry point so the application can be
launched as `python app.py` in addition to `python main.py`.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()
