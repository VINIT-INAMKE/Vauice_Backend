#!/usr/bin/env python
"""
Chat cleanup scheduler for production deployment.
This script can be called by cron jobs to clean up chat data periodically.

Cron job examples:
# Run daily cleanup at 2:00 AM
0 2 * * * cd /path/to/project && python cleanup_scheduler.py daily

# Run weekly cleanup on Sundays at 3:00 AM
0 3 * * 0 cd /path/to/project && python cleanup_scheduler.py weekly

# Run monthly cleanup on the 1st day at 4:00 AM
0 4 1 * * cd /path/to/project && python cleanup_scheduler.py monthly
"""

import os
import sys
import django
from django.core.management import call_command

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def run_cleanup(cleanup_type='daily'):
    """
    Run chat cleanup based on the specified type
    """
    if cleanup_type == 'daily':
        # Daily cleanup: Remove deleted messages older than 7 days
        call_command('cleanup_chat', '--days=7')
    elif cleanup_type == 'weekly':
        # Weekly cleanup: Remove deleted messages older than 30 days
        call_command('cleanup_chat', '--days=30')
    elif cleanup_type == 'monthly':
        # Monthly cleanup: Remove deleted messages older than 365 days (as per settings)
        call_command('cleanup_chat', '--days=365')
    else:
        print(f"Unknown cleanup type: {cleanup_type}")
        print("Available types: daily, weekly, monthly")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cleanup_scheduler.py [daily|weekly|monthly]")
        sys.exit(1)
    
    cleanup_type = sys.argv[1]
    print(f"Running {cleanup_type} chat cleanup...")
    
    try:
        run_cleanup(cleanup_type)
        print(f"{cleanup_type.capitalize()} cleanup completed successfully!")
    except Exception as e:
        print(f"Error during {cleanup_type} cleanup: {str(e)}")
        sys.exit(1)