"""
WSGI config for backend project.
EMERGENCY FIX: Disable Socket.io wrapper completely to restore API functionality
"""

import os
import django
from django.core.wsgi import get_wsgi_application

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Use standard Django WSGI - NO Socket.io wrapper
application = get_wsgi_application()

# TEMPORARY: Socket.io disabled to fix API calls
# We'll implement Socket.io as a separate service or find a different integration method
# This ensures all API calls work normally