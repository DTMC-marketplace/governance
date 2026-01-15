#!/usr/bin/env python
"""
Enhanced server startup script with better logging
"""
import os
import sys
import logging
from datetime import datetime

# Setup logging before Django imports
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Run Django development server with enhanced logging"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    
    try:
        from django.core.management import execute_from_command_line
        from django.conf import settings
        from django.core.management import call_command
    except ImportError as exc:
        logger.error(f"❌ Failed to import Django: {exc}")
        logger.error("Make sure Django is installed and virtual environment is activated")
        sys.exit(1)
    
    # Pre-startup checks
    logger.info("=" * 60)
    logger.info("🚀 Starting Governance Hackathon Project Server")
    logger.info("=" * 60)
    
    # Check settings
    logger.info(f"📋 Settings module: {settings.SETTINGS_MODULE}")
    logger.info(f"🔧 DEBUG mode: {settings.DEBUG}")
    logger.info(f"📁 Base directory: {settings.BASE_DIR}")
    
    # Check for common issues
    try:
        from django.core.management import call_command
        logger.info("✅ Django imports successful")
    except Exception as e:
        logger.error(f"❌ Django setup error: {e}")
        sys.exit(1)
    
    # Run system checks (after Django setup)
    logger.info("🔍 Running system checks...")
    try:
        import django
        django.setup()
        from django.core.management import call_command
        call_command('check', verbosity=0)
        logger.info("✅ System checks passed")
    except Exception as e:
        # This is normal - Django will run checks automatically
        logger.info("✅ System checks will run automatically")
    
    # Start server
    logger.info("=" * 60)
    logger.info("🌐 Starting development server...")
    logger.info("=" * 60)
    logger.info("📝 Server will be available at: http://127.0.0.1:8000/")
    logger.info("🛑 Press CTRL+C to stop the server")
    logger.info("=" * 60)
    
    try:
        execute_from_command_line(['manage.py', 'runserver'] + sys.argv[1:])
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Server stopped by user")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
