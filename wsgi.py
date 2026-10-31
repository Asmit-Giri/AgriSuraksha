"""
WSGI Production Entrypoint for AgriSuraksha
Compatible with Gunicorn, Waitress, uWSGI, and cloud providers (Render, Railway, Heroku).
"""
import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # If run on Windows as production, use Waitress
    if os.name == 'nt':
        try:
            from waitress import serve
            print(f"[Waitress] Serving production server on http://0.0.0.0:{port}...")
            serve(app, host='0.0.0.0', port=port)
        except ImportError:
            app.run(host='0.0.0.0', port=port)
    else:
        app.run(host='0.0.0.0', port=port)

