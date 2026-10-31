"""
Vercel Serverless Function Entrypoint for AgriSuraksha
This file is automatically detected by Vercel's Python runtime (@vercel/python).
"""
import sys
import os

# Add the project root directory to sys.path so modules (app, db, config) can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel needs the WSGI application callable named 'app'
# 'app' is the Flask WSGI instance

