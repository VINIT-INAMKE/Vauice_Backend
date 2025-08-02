from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
# Django Channels removed - using Socket.io for real-time communication
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
import uuid
import logging

from .models import (
    ChatRoom, Message, MessageAttachment, MessageStatus, 
    UserPresence, EncryptionKey, RoomMembership
)
from .serializers import (
    ChatRoomSerializer, ChatRoomCreateSerializer, MessageSerializer,
    MessageCreateSerializer, EncryptionKeySerializer, EncryptionKeyCreateSerializer,
    MessageReadSerializer, FileUploadSerializer, RoomInviteSerializer,
    UserSearchSerializer, UserPresenceSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()
# channel_layer = get_channel_layer()  # Removed - using Socket.io

@method_decorator(ratelimit(key='user', rate='30/m', method='POST', block=True), name='create')
class ChatRoomListView(generics.ListCreateAPIView):
    """List and create chat rooms"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if hasattr(self, 'request') and self.request and self.request.method == 'POST':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer
    
    def get_queryset(self):
        """Get chat rooms for the current user"""
        return ChatRoom.objects.filter(
            participants=self.request.user,
            is_active=True
        ).prefetch_related(
            'participants',
            'created_by',
            Prefetch('messages', queryset=Message.objects.filter(is_deleted=False).order_by('-timestamp')[:1]),
            'memberships__user'
        ).distinct().order_by('-updated_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new chat room"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        participant_ids = serializer.validated_data.pop('participant_ids')
        room_type = serializer.validated_data.get('room_type', 'private')
        
        # For private chats, check if room already exists
        if room_type == 'private':
            other_user_id = participant_ids[0]
            existing_room = ChatRoom.objects.filter(
                room_type='private',
                participants=request.user
            ).filter(
                participants=other_user_id
            ).first()
            
            if existing_room:
                return Response(
                    ChatRoomSerializer(existing_room).data,
                    status=status.HTTP_200_OK
                )
        
        # Create new room
        room = ChatRoom.objects.create(
            created_by=request.user,
            **serializer.validated_data
        )
        
        # Add participants
        participants = User.objects.filter(id__in=participant_ids)
        room.participants.add(request.user)  # Add creator
        room.participants.add(*participants)
        
        # Create memberships
        RoomMembership.objects.create(
            user=request.user,
            room=room,
            role='owner' if room_type == 'group' else 'member'
        )
        
        for participant in participants:
            RoomMembership.objects.create(
                user=participant,
                room=room,
                role='member'
            )
        
        return Response(
            ChatRoomSerializer(room).data,
            status=status.HTTP_201_CREATED
        )

class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a chat room"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChatRoom.objects.none()
        return ChatRoom.objects.filter(
            participants=self.request.user,
            is_active=True
        )

class ChatRoomInviteView(APIView):
    """Invite users to a chat room"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        room = get_object_or_404(ChatRoom, pk=pk, participants=request.user)
        
        # Check if user has permission to invite (admin or owner)
        membership = get_object_or_404(
            RoomMembership,
            user=request.user,
            room=room
        )
        
        if membership.role not in ['admin', 'owner']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RoomInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        users_to_invite = User.objects.filter(id__in=user_ids)
        
        # Filter out users already in the room
        existing_participants = room.participants.values_list('id', flat=True)
        new_users = users_to_invite.exclude(id__in=existing_participants)
        
        # Add new users to room
        room.participants.add(*new_users)
        
        # Create memberships
        for user in new_users:
            RoomMembership.objects.create(
                user=user,
                room=room,
                role='member'
            )
        
        # Real-time notifications now handled by Socket.io
        # Socket.io will handle room invitations via 'invite_to_room' event
        # No need for Django Channels WebSocket calls
        
        return Response(
            {'message': f'{len(new_users)} users invited successfully'},
            status=status.HTTP_200_OK
        )

class ChatRoomLeaveView(APIView):
    """Leave a chat room"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        room = get_object_or_404(ChatRoom, pk=pk, participants=request.user)
        
        try:
            membership = RoomMembership.objects.get(
                user=request.user,
                room=room
            )
            membership.delete()
            room.participants.remove(request.user)
            
            # If it's a group chat and user was the owner, transfer ownership
            if room.room_type == 'group' and membership.role == 'owner':
                next_admin = RoomMembership.objects.filter(
                    room=room,
                    role='admin'
                ).first()
                
                if next_admin:
                    next_admin.role = 'owner'
                    next_admin.save()
                else:
                    # Make the first member the owner
                    first_member = RoomMembership.objects.filter(room=room).first()
                    if first_member:
                        first_member.role = 'owner'
                        first_member.save()
            
            return Response(
                {'message': 'Left room successfully'},
                status=status.HTTP_200_OK
            )
            
        except RoomMembership.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this room'},
                status=status.HTTP_400_BAD_REQUEST
            )

@method_decorator(ratelimit(key='user', rate='60/m', method='POST', block=True), name='create')
class MessageListView(generics.ListCreateAPIView):
    """List messages for a room and create new messages"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if hasattr(self, 'request') and self.request and self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """Get messages for a specific room"""
        room_id = self.request.query_params.get('room_id')
        if not room_id:
            return Message.objects.none()
        
        # Check if user has access to this room
        try:
            room = ChatRoom.objects.get(
                id=room_id,
                participants=self.request.user
            )
        except ChatRoom.DoesNotExist:
            return Message.objects.none()
        
        return Message.objects.filter(
            room=room,
            is_deleted=False
        ).select_related(
            'sender',
            'reply_to__sender'
        ).prefetch_related(
            'attachments',
            'statuses__user'
        ).order_by('-timestamp')
    
    def create(self, request, *args, **kwargs):
        """Create a new message"""
        room_id = request.data.get('room_id')
        if not room_id:
            return Response(
                {'error': 'room_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has access to this room
        try:
            room = ChatRoom.objects.get(
                id=room_id,
                participants=request.user
            )
        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Room not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create message
        message = Message.objects.create(
            room=room,
            sender=request.user,
            **serializer.validated_data
        )
        
        # Handle file attachments
        attachments = request.FILES.getlist('attachments', [])
        for attachment_file in attachments:
            MessageAttachment.objects.create(
                message=message,
                file=attachment_file,
                file_name=attachment_file.name,
                file_size=attachment_file.size,
                file_type=attachment_file.content_type
            )
        
        # Update room timestamp
        room.updated_at = timezone.now()
        room.save()
        
        # Real-time messaging now handled by Socket.io 'send_message' event
        # No need for Django Channels WebSocket calls
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a message"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return Message.objects.filter(
            room__participants=self.request.user,
            is_deleted=False
        )
    
    def update(self, request, *args, **kwargs):
        """Edit a message"""
        message = self.get_object()
        
        # Check if user owns the message
        if message.sender != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update message
        message.encrypted_content = request.data.get('encrypted_content', message.encrypted_content)
        message.content_hash = request.data.get('content_hash', message.content_hash)
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        
        # Real-time message editing now handled by Socket.io 'edit_message' event
        # No need for Django Channels WebSocket calls
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_200_OK
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a message (soft delete)"""
        message = self.get_object()
        
        # Check if user owns the message
        if message.sender != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        message.soft_delete()
        
        # Real-time message deletion now handled by Socket.io 'delete_message' event
        # No need for Django Channels WebSocket calls
        
        return Response(
            {'message': 'Message deleted successfully'},
            status=status.HTTP_200_OK
        )

class MessageMarkAsReadView(APIView):
    """Mark messages as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = MessageReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message_ids = serializer.validated_data['message_ids']
        messages = Message.objects.filter(
            id__in=message_ids,
            room__participants=request.user
        )
        
        # Update or create message statuses
        for message in messages:
            MessageStatus.objects.update_or_create(
                message=message,
                user=request.user,
                defaults={'status': 'read'}
            )
        
        return Response(
            {'message': f'{len(messages)} messages marked as read'},
            status=status.HTTP_200_OK
        )

class EncryptionKeyListView(generics.ListCreateAPIView):
    """List and create encryption keys"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if hasattr(self, 'request') and self.request and self.request.method == 'POST':
            return EncryptionKeyCreateSerializer
        return EncryptionKeySerializer
    
    def get_queryset(self):
        """Get encryption keys for users"""
        user_ids = self.request.query_params.getlist('user_ids')
        if user_ids:
            return EncryptionKey.objects.filter(
                user_id__in=user_ids,
                is_active=True
            ).select_related('user')
        
        # Return current user's keys
        return EncryptionKey.objects.filter(
            user=self.request.user,
            is_active=True
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new encryption key"""
        # Deactivate old keys
        EncryptionKey.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        key = EncryptionKey.objects.create(
            user=request.user,
            **serializer.validated_data
        )
        
        return Response(
            EncryptionKeySerializer(key).data,
            status=status.HTTP_201_CREATED
        )

class UserSearchView(generics.ListAPIView):
    """Search users by username or name"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSearchSerializer
    
    def get_queryset(self):
        """Search users by username or name"""
        query = self.request.query_params.get('q', '')
        if not query or len(query) < 2:
            return User.objects.none()
        
        return User.objects.filter(
            Q(username__icontains=query) |
            Q(firstname__icontains=query) |
            Q(lastname__icontains=query)
        ).exclude(
            id=self.request.user.id
        ).select_related('presence')[:20]

@method_decorator(ratelimit(key='user', rate='20/m', method='POST', block=True), name='post')
class FileUploadView(APIView):
    """Handle file uploads for chat"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data['file']
        file_type = serializer.validated_data['file_type']
        
        # Create a temporary attachment record with expiration
        attachment = MessageAttachment.objects.create(
            message=None,  # Will be linked when message is created
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=uploaded_file.content_type,
            is_encrypted=serializer.validated_data.get('is_encrypted', True),
            encryption_key_id=serializer.validated_data.get('encryption_key_id')
        )
        
        # Schedule cleanup of orphaned attachments after 1 hour
        from django.utils import timezone
        from datetime import timedelta
        cleanup_time = timezone.now() + timedelta(hours=1)
        
        # Log for potential cleanup (you could use Celery for this in production)
        logger.info(f"Temporary attachment {attachment.id} uploaded, cleanup scheduled for {cleanup_time}")
        
        return Response({
            'attachment_id': str(attachment.id),
            'file_url': attachment.file.url,
            'file_name': attachment.file_name,
            'file_size': attachment.file_size,
            'file_type': attachment.file_type
        }, status=status.HTTP_201_CREATED)

class UserPresenceListView(generics.ListAPIView):
    """Get user presence information"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPresenceSerializer
    
    def get_queryset(self):
        """Get presence for users in user's chat rooms"""
        # Get all users that share chat rooms with current user
        user_rooms = ChatRoom.objects.filter(participants=self.request.user)
        shared_users = User.objects.filter(
            chat_rooms__in=user_rooms
        ).exclude(
            id=self.request.user.id
        ).distinct()
        
        return UserPresence.objects.filter(
            user__in=shared_users
        ).select_related('user', 'is_typing_in')