"""
Pharaoh Engine — Egyptian Football Management Game
Main entry point.
"""
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.app import run_app

if __name__ == "__main__":
    run_app()
