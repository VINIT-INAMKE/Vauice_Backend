from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ChatRoom, Message, MessageAttachment, MessageStatus,
    UserPresence, EncryptionKey, RoomMembership
)

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'room_type', 'participant_count', 'created_by', 'created_at', 'is_active']
    list_filter = ['room_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'participants__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['participants']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('participants')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'room', 'message_type', 'timestamp', 'is_edited', 'is_deleted']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'timestamp']
    search_fields = ['sender__username', 'room__name']
    readonly_fields = ['id', 'timestamp', 'edited_at', 'content_hash']
    raw_id_fields = ['room', 'sender', 'reply_to']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'room')

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'file_name', 'file_type', 'file_size_mb', 'is_encrypted', 'uploaded_at']
    list_filter = ['file_type', 'is_encrypted', 'uploaded_at']
    search_fields = ['file_name', 'message__sender__username']
    readonly_fields = ['id', 'uploaded_at']
    raw_id_fields = ['message']
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'File Size'

@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'status', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['user__username', 'message__sender__username']
    readonly_fields = ['timestamp']
    raw_id_fields = ['message', 'user']

@admin.register(UserPresence)
class UserPresenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'last_seen', 'is_typing_indicator', 'typing_started_at']
    list_filter = ['status', 'last_seen']
    search_fields = ['user__username']
    readonly_fields = ['last_seen']
    raw_id_fields = ['user', 'is_typing_in']
    
    def is_typing_indicator(self, obj):
        if obj.is_typing_in:
            return format_html(
                '<span style="color: green;">✓ Typing in {}</span>',
                obj.is_typing_in.name or f'Room {obj.is_typing_in.id}'
            )
        return format_html('<span style="color: gray;">Not typing</span>')
    is_typing_indicator.short_description = 'Typing Status'

@admin.register(EncryptionKey)
class EncryptionKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'key_id', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'key_id']
    readonly_fields = ['created_at', 'public_key_preview']
    raw_id_fields = ['user']
    
    def public_key_preview(self, obj):
        if obj.public_key:
            preview = obj.public_key[:50] + '...' if len(obj.public_key) > 50 else obj.public_key
            return format_html('<code>{}</code>', preview)
        return 'No key'
    public_key_preview.short_description = 'Public Key Preview'

@admin.register(RoomMembership)
class RoomMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'role', 'joined_at', 'notifications_enabled', 'unread_count']
    list_filter = ['role', 'notifications_enabled', 'joined_at']
    search_fields = ['user__username', 'room__name']
    readonly_fields = ['joined_at', 'unread_count']
    raw_id_fields = ['user', 'room', 'last_read_message']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'room')
