"""
URL configuration for Governance Hackathon Standalone Project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('governance.urls')),
]

# Serve static files during development (always serve in development, even if DEBUG=False)
from pathlib import Path
static_root = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None
if static_root:
    # Convert Path object to string for static() helper
    if isinstance(static_root, Path):
        static_root = str(static_root)
    urlpatterns += static(settings.STATIC_URL, document_root=static_root)
