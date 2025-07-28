from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import Message, MessageAttachment, EncryptionKey
from chat.encryption import SecurityUtils
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up old chat data and expired encryption keys'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days to keep deleted messages (default: 365)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Starting chat cleanup (keeping {days} days of data)")
        
        # Clean up soft-deleted messages older than specified days
        cutoff_date = timezone.now() - timedelta(days=days)
        
        old_messages = Message.objects.filter(
            is_deleted=True,
            timestamp__lt=cutoff_date
        )
        
        message_count = old_messages.count()
        
        if dry_run:
            self.stdout.write(f"Would delete {message_count} old messages")
        else:
            # Delete associated attachments first
            old_attachments = MessageAttachment.objects.filter(
                message__in=old_messages
            )
            attachment_count = old_attachments.count()
            old_attachments.delete()
            
            # Delete messages
            old_messages.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {message_count} old messages and {attachment_count} attachments"
                )
            )
        
        # Clean up expired encryption keys
        if dry_run:
            self.stdout.write("Would clean up expired encryption keys")
        else:
            cleaned_keys = SecurityUtils.clean_expired_keys()
            self.stdout.write(
                self.style.SUCCESS(f"Cleaned up {cleaned_keys} expired encryption keys")
            )
        
        self.stdout.write(self.style.SUCCESS("Chat cleanup completed"))
