from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ChatRoom, Message, MessageAttachment, MessageStatus, 
    UserPresence, EncryptionKey, RoomMembership
)

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Enhanced user serializer for chat contexts with profile data"""
    avatar_url = serializers.SerializerMethodField()
    profile_data = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'firstname', 'lastname', 'full_name', 
            'user_type', 'gender', 'age', 'avatar_url', 'profile_data'
        ]
        
    def get_avatar_url(self, obj):
        # Check both user avatar and profile picture
        if hasattr(obj, 'avatar') and obj.avatar:
            return obj.avatar.url
        
        # Check profile-specific avatar
        try:
            if obj.user_type == 'talent' and hasattr(obj, 'talent_profile'):
                if obj.talent_profile.profile_picture:
                    return obj.talent_profile.profile_picture.url
            elif obj.user_type == 'mentor' and hasattr(obj, 'mentor_profile'):
                if obj.mentor_profile.profile_picture:
                    return obj.mentor_profile.profile_picture.url
        except:
            pass
            
        return None
    
    def get_profile_data(self, obj):
        """Get user-type specific profile data for richer chat context"""
        try:
            if obj.user_type == 'talent' and hasattr(obj, 'talent_profile'):
                profile = obj.talent_profile
                return {
                    'bio': profile.bio[:100] + '...' if len(profile.bio) > 100 else profile.bio,
                    'selected_sports': profile.selected_sports[:3] if isinstance(profile.selected_sports, list) else [],
                    'experience_years': profile.experience_years,
                    'is_verified': profile.is_verified,
                    'is_featured': profile.is_featured,
                    'location': f"{profile.city}, {profile.state}" if profile.city and profile.state else profile.location
                }
            elif obj.user_type == 'mentor' and hasattr(obj, 'mentor_profile'):
                profile = obj.mentor_profile
                return {
                    'bio': profile.bio[:100] + '...' if len(profile.bio) > 100 else profile.bio,
                    'selected_sports': profile.selected_sports[:3] if isinstance(profile.selected_sports, list) else [],
                    'coaching_experience_years': profile.coaching_experience_years,
                    'coaching_levels': profile.coaching_levels,
                    'is_verified': profile.is_verified,
                    'is_available': profile.is_available,
                    'location': f"{profile.city}, {profile.state}" if profile.city and profile.state else profile.location
                }
        except:
            pass
            
        return {}

class UserPresenceSerializer(serializers.ModelSerializer):
    """User presence serializer"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = UserPresence
        fields = ['user', 'status', 'last_seen', 'is_typing_in']

class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Message attachment serializer"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'file_url', 'file_name', 'file_size', 
            'file_type', 'is_encrypted', 'uploaded_at'
        ]
        
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

class MessageStatusSerializer(serializers.ModelSerializer):
    """Message status serializer"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MessageStatus
        fields = ['user', 'status', 'timestamp']

class MessageSerializer(serializers.ModelSerializer):
    """Message serializer with encryption support"""
    sender = UserBasicSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    statuses = MessageStatusSerializer(many=True, read_only=True)
    reply_to = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'encrypted_content', 
            'content_hash', 'timestamp', 'edited_at', 'is_edited',
            'is_deleted', 'reply_to', 'attachments', 'statuses'
        ]
        read_only_fields = ['id', 'sender', 'timestamp', 'edited_at', 'is_edited']
        
    def get_reply_to(self, obj):
        if obj.reply_to:
            return {
                'id': str(obj.reply_to.id),
                'sender': UserBasicSerializer(obj.reply_to.sender).data,
                'message_type': obj.reply_to.message_type,
                'timestamp': obj.reply_to.timestamp
            }
        return None

class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Message
        fields = [
            'encrypted_content', 'content_hash', 'message_type', 
            'reply_to', 'attachments'
        ]
        
    def validate_encrypted_content(self, value):
        if not value and self.initial_data.get('message_type') == 'text':
            raise serializers.ValidationError("Encrypted content is required for text messages")
        return value

class RoomMembershipSerializer(serializers.ModelSerializer):
    """Room membership serializer"""
    user = UserBasicSerializer(read_only=True)
    unread_count = serializers.ReadOnlyField()
    
    class Meta:
        model = RoomMembership
        fields = [
            'user', 'role', 'joined_at', 'last_read_message',
            'notifications_enabled', 'unread_count'
        ]

class ChatRoomSerializer(serializers.ModelSerializer):
    """Chat room serializer"""
    participants = UserBasicSerializer(many=True, read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    last_message = MessageSerializer(read_only=True)
    memberships = RoomMembershipSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'participants', 'created_by',
            'created_at', 'updated_at', 'is_active', 'description',
            'avatar_url', 'last_message', 'memberships', 'participant_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
        
    def get_participant_count(self, obj):
        return obj.participants.count()
        
    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms"""
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    
    class Meta:
        model = ChatRoom
        fields = ['name', 'room_type', 'description', 'participant_ids']
        
    def validate_participant_ids(self, value):
        # Check if all participant IDs exist
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError("One or more participant IDs are invalid")
        return value
        
    def validate(self, data):
        # For private chats, ensure only 2 participants (including creator)
        if data.get('room_type') == 'private' and len(data.get('participant_ids', [])) != 1:
            raise serializers.ValidationError(
                "Private chats must have exactly 2 participants (including yourself)"
            )
        return data

class EncryptionKeySerializer(serializers.ModelSerializer):
    """Encryption key serializer"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = EncryptionKey
        fields = ['id', 'user', 'key_id', 'public_key', 'created_at', 'is_active']
        read_only_fields = ['id', 'user', 'created_at']

class EncryptionKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating encryption keys"""
    
    class Meta:
        model = EncryptionKey
        fields = ['key_id', 'public_key']
        
    def validate_key_id(self, value):
        # Ensure key_id is unique for this user
        user = self.context['request'].user
        if EncryptionKey.objects.filter(user=user, key_id=value, is_active=True).exists():
            raise serializers.ValidationError("Key ID already exists for this user")
        return value

class MessageReadSerializer(serializers.Serializer):
    """Serializer for marking messages as read"""
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    
    def validate_message_ids(self, value):
        # Check if all message IDs exist
        existing_messages = Message.objects.filter(id__in=value).count()
        if existing_messages != len(value):
            raise serializers.ValidationError("One or more message IDs are invalid")
        return value

class FileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads"""
    file = serializers.FileField(required=True)
    file_type = serializers.ChoiceField(
        choices=['image', 'video', 'audio', 'document'],
        required=True
    )
    is_encrypted = serializers.BooleanField(default=True)
    encryption_key_id = serializers.CharField(required=False, allow_blank=True)
    
    def validate_file(self, value):
        # Validate file size (50MB max)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 50MB")
        return value

class RoomInviteSerializer(serializers.Serializer):
    """Serializer for inviting users to rooms"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    
    def validate_user_ids(self, value):
        # Check if all user IDs exist
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError("One or more user IDs are invalid")
        return value

class UserSearchSerializer(serializers.ModelSerializer):
    """Enhanced serializer for user search results with profile context"""
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    profile_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'firstname', 'lastname', 'full_name', 
            'user_type', 'avatar_url', 'is_online', 'profile_summary'
        ]
        
    def get_avatar_url(self, obj):
        # Check both user avatar and profile picture
        if hasattr(obj, 'avatar') and obj.avatar:
            return obj.avatar.url
            
        # Check profile-specific avatar
        try:
            if obj.user_type == 'talent' and hasattr(obj, 'talent_profile'):
                if obj.talent_profile.profile_picture:
                    return obj.talent_profile.profile_picture.url
            elif obj.user_type == 'mentor' and hasattr(obj, 'mentor_profile'):
                if obj.mentor_profile.profile_picture:
                    return obj.mentor_profile.profile_picture.url
        except:
            pass
            
        return None
        
    def get_is_online(self, obj):
        try:
            return obj.presence.status == 'online'
        except:
            return False
    
    def get_profile_summary(self, obj):
        """Get brief profile summary for search context"""
        try:
            if obj.user_type == 'talent' and hasattr(obj, 'talent_profile'):
                profile = obj.talent_profile
                sports = profile.selected_sports[:3] if isinstance(profile.selected_sports, list) else []
                return {
                    'sports': sports,
                    'experience_years': profile.experience_years,
                    'is_verified': profile.is_verified,
                    'location': f"{profile.city}, {profile.state}" if profile.city and profile.state else None
                }
            elif obj.user_type == 'mentor' and hasattr(obj, 'mentor_profile'):
                profile = obj.mentor_profile
                sports = profile.selected_sports[:3] if isinstance(profile.selected_sports, list) else []
                return {
                    'sports': sports,
                    'coaching_experience': profile.coaching_experience_years,
                    'coaching_level': profile.coaching_levels,
                    'is_verified': profile.is_verified,
                    'is_available': profile.is_available,
                    'location': f"{profile.city}, {profile.state}" if profile.city and profile.state else None
                }
        except:
            pass
            
        return {}
