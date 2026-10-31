"""
Root entrypoint for Vercel and WSGI servers.
Exposes the Flask WSGI 'app' instance.
"""
from app import app

if __name__ == '__main__':
    app.run()
