from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'recipient', 'sender', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message_text', 'recipient__username', 'sender__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('recipient', 'sender', 'talent', 'mentor', 'chat_room', 'message')
