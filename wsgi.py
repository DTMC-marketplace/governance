"""
WSGI config for Governance project.
Used for production (Azure Web App: gunicorn wsgi:application).

- Local dev: dùng python run_server.py (Django dev server).
- Azure:     Startup Command = gunicorn ... wsgi:application (xem DEPLOY_AZURE.md).
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
