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

# Serve static files (always serve, even if DEBUG=False)
from django.views.static import serve
from django.urls import re_path
from pathlib import Path

static_root = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None
if static_root:
    if isinstance(static_root, Path):
        static_root = str(static_root)
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': static_root}),
    ]
