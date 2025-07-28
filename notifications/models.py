from django.db import models
from django.conf import settings
from talent.models import TalentProfile
from mentor.models import MentorProfile
from chat.models import ChatRoom, Message

NOTIFICATION_TYPES = [
    ('mentor_selected', 'Mentor Selected Talent'),
    ('talent_rejected', 'Mentor Rejected Talent'),
    ('new_message', 'New Chat Message'),
    ('chat_room_created', 'Chat Room Created'),
]

class Notification(models.Model):
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    
    # Optional references to related objects
    talent = models.ForeignKey(TalentProfile, on_delete=models.CASCADE, null=True, blank=True)
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, null=True, blank=True)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    message_text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"
