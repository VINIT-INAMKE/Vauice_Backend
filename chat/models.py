from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField
import uuid

User = get_user_model()

class ChatRoom(models.Model):
    """Chat room model for private and group conversations"""
    ROOM_TYPES = (
        ('private', 'Private Chat'),
        ('group', 'Group Chat'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)  # For group chats
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='private')
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Group chat specific fields
    description = models.TextField(blank=True, null=True)
    avatar = CloudinaryField('image', blank=True, null=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['room_type', 'is_active']),
            models.Index(fields=['created_by']),
        ]
        
    def __str__(self):
        if self.room_type == 'group' and self.name:
            return self.name
        elif self.room_type == 'private':
            participants = list(self.participants.all())
            if len(participants) >= 2:
                return f"Chat between {participants[0].username} and {participants[1].username}"
        return f"Room {self.id}"
    
    @property
    def last_message(self):
        return self.messages.filter(is_deleted=False).last()
    
    def get_other_participant(self, user):
        """Get the other participant in a private chat"""
        if self.room_type == 'private':
            return self.participants.exclude(id=user.id).first()
        return None

class Message(models.Model):
    """Message model with encryption support"""
    MESSAGE_TYPES = (
        ('text', 'Text Message'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
        ('system', 'System Message'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    
    # Encrypted content - never store plaintext on server
    encrypted_content = models.TextField(blank=True, null=True)  # Encrypted message content
    content_hash = models.CharField(max_length=64, blank=True, null=True)  # For integrity verification
    
    # Metadata (not encrypted)
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Reply functionality
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='replies')
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['room', 'is_deleted']),
            models.Index(fields=['room', 'is_deleted', 'timestamp']),
            models.Index(fields=['message_type']),
        ]
        
    def __str__(self):
        return f"Message from {self.sender.username} in {self.room}"
    
    def soft_delete(self):
        """Soft delete message"""
        self.is_deleted = True
        self.encrypted_content = None
        self.save()

class MessageAttachment(models.Model):
    """File attachments for messages"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = CloudinaryField('raw', blank=True, null=True)  # For files
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)  # MIME type
    
    # Encryption metadata for files
    is_encrypted = models.BooleanField(default=True)
    encryption_key_id = models.CharField(max_length=255, blank=True, null=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment: {self.file_name}"

class MessageStatus(models.Model):
    """Track message delivery and read status"""
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    )
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['message', 'user']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'timestamp']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.status} - {self.message.id}"

class UserPresence(models.Model):
    """Track user online/offline status"""
    STATUS_CHOICES = (
        ('online', 'Online'),
        ('away', 'Away'),
        ('offline', 'Offline'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField(auto_now=True)
    is_typing_in = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, blank=True, null=True, related_name='typing_users')
    typing_started_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
    def set_online(self):
        self.status = 'online'
        self.last_seen = timezone.now()
        self.save()
    
    def set_offline(self):
        self.status = 'offline'
        self.is_typing_in = None
        self.typing_started_at = None
        self.save()
    
    def start_typing(self, room):
        self.is_typing_in = room
        self.typing_started_at = timezone.now()
        self.save()
    
    def stop_typing(self):
        self.is_typing_in = None
        self.typing_started_at = None
        self.save()

class EncryptionKey(models.Model):
    """Store public keys for end-to-end encryption"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='encryption_keys')
    key_id = models.CharField(max_length=255, unique=True)
    public_key = models.TextField()  # Base64 encoded public key
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Key {self.key_id} for {self.user.username}"

class RoomMembership(models.Model):
    """Track user membership in chat rooms with additional metadata"""
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_message = models.ForeignKey(Message, on_delete=models.SET_NULL, blank=True, null=True)
    notifications_enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'room']
        indexes = [
            models.Index(fields=['user', 'room']),
            models.Index(fields=['room', 'role']),
            models.Index(fields=['user', 'notifications_enabled']),
            models.Index(fields=['joined_at']),
        ]
        
    def __str__(self):
        return f"{self.user.username} in {self.room} ({self.role})"
    
    @property
    def unread_count(self):
        if not self.last_read_message:
            return self.room.messages.filter(is_deleted=False).count()
        return self.room.messages.filter(
            timestamp__gt=self.last_read_message.timestamp,
            is_deleted=False
        ).count()
