"""
Django settings for Governance Hackathon Standalone Project
No database, no authentication, no security - for demo only
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: keep the secret key used in production secret!
# In production (e.g. Azure), set SECRET_KEY in Application Settings / environment variables.
SECRET_KEY = os.environ.get("SECRET_KEY", "hackathon-demo-only-not-for-production")

# SECURITY WARNING: don't run with debug turned on in production!
# Set DEBUG=False in Azure Application Settings for production.
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

# In production, set ALLOWED_HOSTS as comma-separated list in env, e.g. your-app.azurewebsites.net
_allowed = os.environ.get("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",")] if _allowed else ["*"]

# Application definition
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'governance',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'urls'

# NO DATABASE
DATABASES = {}

# NO AUTHENTICATION
AUTHENTICATION_BACKENDS = []

# Internationalization
TIME_ZONE = 'UTC'
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'governance.context_processors.csrf_token',
            ],
        },
    },
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AI Act / Gemini API Configuration
# SECURITY: API keys should be loaded from environment variables in production
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
AI_ACT_ARTICLES_DIR = BASE_DIR / 'ai_act_articles'
AI_ACT_STORE_INFO_PATH = BASE_DIR / 'ai_act_store_info.txt'
AI_ACT_STORE_NAME = os.environ.get('AI_ACT_STORE_NAME', '')
# Free tier models: gemini-2.5-flash, gemini-2.5-flash-lite, gemini-3-flash-preview
# Note: gemini-1.5-* models are deprecated
AI_ACT_MODEL_NAME = os.environ.get('AI_ACT_MODEL_NAME', 'gemini-2.5-flash')
# Use File Search (slower but more accurate) or manual context (faster)
# Set to False to skip File Search and use manual context directly for faster responses
# Used in: governance/infrastructure/services/gemini_ai_act_service.py (self.use_file_search)
#          governance/views.py api_check_store_info (for debug display)
AI_ACT_USE_FILE_SEARCH = os.environ.get('AI_ACT_USE_FILE_SEARCH', 'False').lower() == 'true'
# API timeout in seconds
AI_ACT_API_TIMEOUT = int(os.environ.get('AI_ACT_API_TIMEOUT', '30'))

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'governance': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'governance.presentation.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'governance.infrastructure.services': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
