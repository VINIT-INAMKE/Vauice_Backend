"""
Complete Socket.IO implementation for Vauice Chat System
No Redis required - perfect for single-server deployment
"""

import socketio
import json
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from .models import ChatRoom, Message, UserPresence, MessageStatus, RoomMembership
from notifications.utils import send_new_message_notification
import logging
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()

# Create Socket.IO server (no Redis needed for single-server deployment)
sio = socketio.Server(
    cors_allowed_origins=["*"],
    cors_credentials=True,
    logger=True,  # Enable logging for debugging
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    allow_upgrades=True,
    transports=['polling', 'websocket']
)

# In-memory storage for user sessions and rooms
user_sessions = {}  # {user_id: {'session_id': sid, 'room_ids': set(), 'user': user_obj}}
room_sessions = {}  # {room_id: {session_ids}}

def authenticate_user(token):
    """Authenticate user from JWT token"""
    try:
        if not token:
            return None
            
        # Remove Bearer prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
            
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        return user
    except (InvalidToken, TokenError, Exception) as e:
        logger.error(f"Authentication error: {str(e)}")
        return None

def get_user_from_session(sid):
    """Get user object from session ID"""
    for user_id, session_data in user_sessions.items():
        if session_data['session_id'] == sid:
            return session_data['user']
    return None

@sio.event
def connect(sid, environ, auth):
    """Handle client connection"""
    try:
        logger.info(f"Connection attempt from {sid}")
        
        # Get token from auth data
        token = auth.get('token') if auth else None
        user = authenticate_user(token)
        
        if not user or isinstance(user, AnonymousUser):
            logger.warning(f"Unauthorized connection attempt: {sid}")
            sio.disconnect(sid)
            return False
            
        # Store user session
        user_sessions[user.id] = {
            'session_id': sid,
            'room_ids': set(),
            'user': user
        }
        
        # Set user as online
        try:
            presence, created = UserPresence.objects.get_or_create(user=user)
            presence.set_online()
        except Exception as e:
            logger.error(f"Error setting user online: {str(e)}")
        
        logger.info(f"User {user.username} connected with session {sid}")
        
        # Send success response
        sio.emit('connected', {
            'status': 'success', 
            'user_id': str(user.id),
            'message': 'Successfully connected to Vauice Chat'
        }, room=sid)
        
        return True
        
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        sio.disconnect(sid)
        return False

@sio.event
def disconnect(sid):
    """Handle client disconnection"""
    try:
        # Find and remove user session
        user_id_to_remove = None
        user = None
        
        for user_id, session_data in user_sessions.items():
            if session_data['session_id'] == sid:
                user_id_to_remove = user_id
                user = session_data['user']
                break
                
        if user_id_to_remove:
            user_data = user_sessions[user_id_to_remove]
            
            # Leave all rooms and notify other users
            for room_id in user_data['room_ids'].copy():
                if room_id in room_sessions:
                    room_sessions[room_id].discard(sid)
                    # Notify other users in room
                    sio.emit('user_left', {
                        'user_id': str(user.id),
                        'username': user.username,
                        'room_id': room_id
                    }, room=room_id)
            
            # Set user as offline
            try:
                presence = UserPresence.objects.get(user=user)
                presence.set_offline()
            except UserPresence.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f"Error setting user offline: {str(e)}")
            
            # Remove user session
            del user_sessions[user_id_to_remove]
            logger.info(f"User {user.username} disconnected")
            
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")

@sio.event
def join_room(sid, data):
    """Join a chat room"""
    try:
        room_id = data.get('room_id')
        if not room_id:
            sio.emit('error', {'message': 'Room ID required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Check room access
        try:
            room = ChatRoom.objects.get(id=room_id, participants=user)
        except ChatRoom.DoesNotExist:
            sio.emit('error', {'message': 'Room not found or access denied'}, room=sid)
            return
            
        # Join Socket.IO room
        sio.enter_room(sid, room_id)
        
        # Track room membership
        if room_id not in room_sessions:
            room_sessions[room_id] = set()
        room_sessions[room_id].add(sid)
        user_sessions[user.id]['room_ids'].add(room_id)
        
        # Notify others in room that user joined
        sio.emit('user_joined', {
            'user_id': str(user.id),
            'username': user.username,
            'room_id': room_id
        }, room=room_id, skip_sid=sid)
        
        # Send success response to user
        sio.emit('joined_room', {
            'room_id': room_id,
            'status': 'success',
            'message': f'Successfully joined room {room_id}'
        }, room=sid)
        
        logger.info(f"User {user.username} joined room {room_id}")
        
    except Exception as e:
        logger.error(f"Join room error: {str(e)}")
        sio.emit('error', {'message': 'Failed to join room'}, room=sid)

@sio.event
def leave_room(sid, data):
    """Leave a chat room"""
    try:
        room_id = data.get('room_id')
        if not room_id:
            return
            
        user = get_user_from_session(sid)
        if not user:
            return
            
        # Leave Socket.IO room
        sio.leave_room(sid, room_id)
        
        # Update tracking
        if room_id in room_sessions:
            room_sessions[room_id].discard(sid)
        if user.id in user_sessions:
            user_sessions[user.id]['room_ids'].discard(room_id)
        
        # Notify others that user left
        sio.emit('user_left', {
            'user_id': str(user.id),
            'username': user.username,
            'room_id': room_id
        }, room=room_id)
        
        logger.info(f"User {user.username} left room {room_id}")
        
    except Exception as e:
        logger.error(f"Leave room error: {str(e)}")

@sio.event
def send_message(sid, data):
    """Send a chat message"""
    try:
        room_id = data.get('room_id')
        encrypted_content = data.get('encrypted_content')
        content_hash = data.get('content_hash')
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to')
        
        if not room_id or not encrypted_content:
            sio.emit('error', {'message': 'Room ID and content required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Verify room access
        try:
            room = ChatRoom.objects.get(id=room_id, participants=user)
        except ChatRoom.DoesNotExist:
            sio.emit('error', {'message': 'Room not found or access denied'}, room=sid)
            return
            
        # Handle reply-to message
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id, room=room)
            except Message.DoesNotExist:
                pass
                
        # Save message to database
        message = Message.objects.create(
            room=room,
            sender=user,
            encrypted_content=encrypted_content,
            content_hash=content_hash,
            message_type=message_type,
            reply_to=reply_to
        )
        
        # Update room timestamp
        room.updated_at = timezone.now()
        room.save()
        
        # Create message data for broadcast
        message_data = {
            'type': 'new_message',
            'message_id': str(message.id),
            'room_id': str(room.id),
            'sender_id': str(user.id),
            'sender_username': user.username,
            'encrypted_content': encrypted_content,
            'content_hash': content_hash,
            'message_type': message_type,
            'timestamp': message.timestamp.isoformat(),
            'is_edited': False,
            'reply_to': str(reply_to.id) if reply_to else None
        }
        
        # Send to all users in room
        sio.emit('new_message', message_data, room=room_id)
        
        # Update message statuses for other participants
        room_participants = room.participants.exclude(id=user.id)
        for participant in room_participants:
            MessageStatus.objects.update_or_create(
                message=message,
                user=participant,
                defaults={'status': 'delivered'}
            )
            
        # Send push notification
        try:
            send_new_message_notification(message)
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            
        logger.info(f"Message sent by {user.username} in room {room_id}")
        
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        sio.emit('error', {'message': 'Failed to send message'}, room=sid)

@sio.event
def start_typing(sid, data):
    """Handle typing start"""
    try:
        room_id = data.get('room_id')
        if not room_id:
            return
            
        user = get_user_from_session(sid)
        if not user:
            return
            
        # Update typing status in database
        try:
            presence, created = UserPresence.objects.get_or_create(user=user)
            room = ChatRoom.objects.get(id=room_id)
            presence.start_typing(room)
        except Exception as e:
            logger.error(f"Error updating typing status: {str(e)}")
            
        # Broadcast typing indicator to other users in room
        sio.emit('typing_indicator', {
            'user_id': str(user.id),
            'username': user.username,
            'is_typing': True,
            'room_id': room_id
        }, room=room_id, skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Start typing error: {str(e)}")

@sio.event
def stop_typing(sid, data):
    """Handle typing stop"""
    try:
        room_id = data.get('room_id')
        if not room_id:
            return
            
        user = get_user_from_session(sid)
        if not user:
            return
            
        # Update typing status in database
        try:
            presence = UserPresence.objects.get(user=user)
            presence.stop_typing()
        except UserPresence.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error updating typing status: {str(e)}")
            
        # Broadcast typing stopped to other users in room
        sio.emit('typing_indicator', {
            'user_id': str(user.id),
            'username': user.username,
            'is_typing': False,
            'room_id': room_id
        }, room=room_id, skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Stop typing error: {str(e)}")

@sio.event
def mark_messages_read(sid, data):
    """Mark messages as read"""
    try:
        message_ids = data.get('message_ids', [])
        if not message_ids:
            return
            
        user = get_user_from_session(sid)
        if not user:
            return
            
        # Update message statuses
        messages = Message.objects.filter(
            id__in=message_ids,
            room__participants=user
        )
        
        for message in messages:
            MessageStatus.objects.update_or_create(
                message=message,
                user=user,
                defaults={'status': 'read'}
            )
            
        logger.info(f"User {user.username} marked {len(messages)} messages as read")
        
    except Exception as e:
        logger.error(f"Mark messages read error: {str(e)}")

@sio.event
def edit_message(sid, data):
    """Edit a message"""
    try:
        message_id = data.get('message_id')
        new_encrypted_content = data.get('encrypted_content')
        new_content_hash = data.get('content_hash')
        
        if not message_id or not new_encrypted_content:
            sio.emit('error', {'message': 'Message ID and content required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Get and verify message ownership
        try:
            message = Message.objects.get(
                id=message_id,
                sender=user,
                is_deleted=False
            )
        except Message.DoesNotExist:
            sio.emit('error', {'message': 'Message not found or access denied'}, room=sid)
            return
            
        # Update message
        message.encrypted_content = new_encrypted_content
        message.content_hash = new_content_hash
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        
        # Broadcast update to room
        message_data = {
            'type': 'message_edited',
            'message_id': str(message.id),
            'room_id': str(message.room.id),
            'encrypted_content': new_encrypted_content,
            'content_hash': new_content_hash,
            'edited_at': message.edited_at.isoformat()
        }
        
        sio.emit('message_edited', message_data, room=str(message.room.id))
        
        logger.info(f"Message {message_id} edited by {user.username}")
        
    except Exception as e:
        logger.error(f"Edit message error: {str(e)}")
        sio.emit('error', {'message': 'Failed to edit message'}, room=sid)

@sio.event
def delete_message(sid, data):
    """Delete a message"""
    try:
        message_id = data.get('message_id')
        
        if not message_id:
            sio.emit('error', {'message': 'Message ID required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Get and verify message ownership
        try:
            message = Message.objects.get(
                id=message_id,
                sender=user,
                is_deleted=False
            )
        except Message.DoesNotExist:
            sio.emit('error', {'message': 'Message not found or access denied'}, room=sid)
            return
            
        # Soft delete message
        message.soft_delete()
        
        # Broadcast deletion to room
        delete_data = {
            'type': 'message_deleted',
            'message_id': str(message.id),
            'room_id': str(message.room.id),
            'deleted_by': str(user.id)
        }
        
        sio.emit('message_deleted', delete_data, room=str(message.room.id))
        
        logger.info(f"Message {message_id} deleted by {user.username}")
        
    except Exception as e:
        logger.error(f"Delete message error: {str(e)}")
        sio.emit('error', {'message': 'Failed to delete message'}, room=sid)

@sio.event
def get_online_users(sid, data):
    """Get list of online users"""
    try:
        user = get_user_from_session(sid)
        if not user:
            return
            
        # Get all online users that share rooms with current user
        user_rooms = ChatRoom.objects.filter(participants=user)
        shared_users = User.objects.filter(chat_rooms__in=user_rooms).distinct()
        
        online_users = []
        for shared_user in shared_users:
            if shared_user.id in user_sessions:
                online_users.append({
                    'user_id': str(shared_user.id),
                    'username': shared_user.username,
                    'is_online': True
                })
                
        sio.emit('online_users', {'users': online_users}, room=sid)
        
    except Exception as e:
        logger.error(f"Get online users error: {str(e)}")

@sio.event
def upload_file(sid, data):
    """Handle file upload for messages"""
    try:
        room_id = data.get('room_id')
        file_data = data.get('file_data')  # Base64 encoded file
        file_name = data.get('file_name')
        file_type = data.get('file_type')
        file_size = data.get('file_size')
        is_encrypted = data.get('is_encrypted', True)
        encryption_key_id = data.get('encryption_key_id')
        
        if not room_id or not file_data or not file_name:
            sio.emit('error', {'message': 'Room ID, file data, and file name required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Verify room access
        try:
            room = ChatRoom.objects.get(id=room_id, participants=user)
        except ChatRoom.DoesNotExist:
            sio.emit('error', {'message': 'Room not found or access denied'}, room=sid)
            return
            
        # Create message for file
        message = Message.objects.create(
            room=room,
            sender=user,
            message_type='file',
            encrypted_content=f"File: {file_name}",
            content_hash=data.get('content_hash', '')
        )
        
        # Create file attachment
        from .models import MessageAttachment
        attachment = MessageAttachment.objects.create(
            message=message,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            is_encrypted=is_encrypted,
            encryption_key_id=encryption_key_id
        )
        
        # For demo purposes, we'll store the file data in the database
        # In production, upload to Cloudinary or S3
        # attachment.file = file_data  # This would be handled by Cloudinary
        
        # Update room timestamp
        room.updated_at = timezone.now()
        room.save()
        
        # Broadcast file message to room
        file_message_data = {
            'type': 'file_message',
            'message_id': str(message.id),
            'room_id': str(room.id),
            'sender_id': str(user.id),
            'sender_username': user.username,
            'file_name': file_name,
            'file_type': file_type,
            'file_size': file_size,
            'attachment_id': str(attachment.id),
            'is_encrypted': is_encrypted,
            'timestamp': message.timestamp.isoformat()
        }
        
        sio.emit('new_file', file_message_data, room=room_id)
        
        # Update message statuses
        room_participants = room.participants.exclude(id=user.id)
        for participant in room_participants:
            MessageStatus.objects.update_or_create(
                message=message,
                user=participant,
                defaults={'status': 'delivered'}
            )
            
        logger.info(f"File uploaded by {user.username} in room {room_id}: {file_name}")
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        sio.emit('error', {'message': 'Failed to upload file'}, room=sid)

@sio.event  
def download_file(sid, data):
    """Handle file download request"""
    try:
        attachment_id = data.get('attachment_id')
        
        if not attachment_id:
            sio.emit('error', {'message': 'Attachment ID required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Get attachment and verify access
        try:
            from .models import MessageAttachment
            attachment = MessageAttachment.objects.get(
                id=attachment_id,
                message__room__participants=user
            )
        except MessageAttachment.DoesNotExist:
            sio.emit('error', {'message': 'File not found or access denied'}, room=sid)
            return
            
        # Send file data back to user
        file_response = {
            'attachment_id': str(attachment.id),
            'file_name': attachment.file_name,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'is_encrypted': attachment.is_encrypted,
            'download_url': str(attachment.file.url) if attachment.file else None
        }
        
        sio.emit('file_download', file_response, room=sid)
        
        logger.info(f"File download requested by {user.username}: {attachment.file_name}")
        
    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        sio.emit('error', {'message': 'Failed to download file'}, room=sid)

@sio.event
def get_room_history(sid, data):
    """Get message history for a room"""
    try:
        room_id = data.get('room_id')
        limit = data.get('limit', 50)
        offset = data.get('offset', 0)
        
        if not room_id:
            sio.emit('error', {'message': 'Room ID required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Verify room access
        try:
            room = ChatRoom.objects.get(id=room_id, participants=user)
        except ChatRoom.DoesNotExist:
            sio.emit('error', {'message': 'Room not found or access denied'}, room=sid)
            return
            
        # Get messages with pagination
        messages = Message.objects.filter(
            room=room,
            is_deleted=False
        ).select_related('sender', 'reply_to').order_by('-timestamp')[offset:offset+limit]
        
        message_list = []
        for message in reversed(messages):  # Reverse to get chronological order
            message_data = {
                'message_id': str(message.id),
                'sender_id': str(message.sender.id),
                'sender_username': message.sender.username,
                'encrypted_content': message.encrypted_content,
                'content_hash': message.content_hash,
                'message_type': message.message_type,
                'timestamp': message.timestamp.isoformat(),
                'is_edited': message.is_edited,
                'edited_at': message.edited_at.isoformat() if message.edited_at else None,
                'reply_to': str(message.reply_to.id) if message.reply_to else None
            }
            message_list.append(message_data)
        
        # Send message history
        history_response = {
            'room_id': room_id,
            'messages': message_list,
            'total_count': Message.objects.filter(room=room, is_deleted=False).count(),
            'has_more': offset + limit < Message.objects.filter(room=room, is_deleted=False).count()
        }
        
        sio.emit('room_history', history_response, room=sid)
        
        logger.info(f"Room history sent to {user.username} for room {room_id}")
        
    except Exception as e:
        logger.error(f"Get room history error: {str(e)}")
        sio.emit('error', {'message': 'Failed to get room history'}, room=sid)

@sio.event
def create_room(sid, data):
    """Create a new chat room"""
    try:
        room_name = data.get('room_name')
        room_type = data.get('room_type', 'private')
        participant_ids = data.get('participant_ids', [])
        description = data.get('description', '')
        
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Create the room
        room = ChatRoom.objects.create(
            name=room_name,
            room_type=room_type,
            created_by=user,
            description=description
        )
        
        # Add creator as participant
        room.participants.add(user)
        
        # Add other participants
        if participant_ids:
            try:
                participants = User.objects.filter(id__in=participant_ids)
                room.participants.add(*participants)
            except Exception as e:
                logger.error(f"Error adding participants: {str(e)}")
        
        # Create membership records
        from .models import RoomMembership
        RoomMembership.objects.create(
            user=user,
            room=room,
            role='owner'
        )
        
        for participant_id in participant_ids:
            try:
                participant = User.objects.get(id=participant_id)
                RoomMembership.objects.create(
                    user=participant,
                    room=room,
                    role='member'
                )
            except User.DoesNotExist:
                continue
        
        # Send room created response
        room_data = {
            'room_id': str(room.id),
            'room_name': room.name,
            'room_type': room.room_type,
            'description': room.description,
            'created_by': user.username,
            'created_at': room.created_at.isoformat(),
            'participants': [
                {
                    'user_id': str(p.id),
                    'username': p.username
                } for p in room.participants.all()
            ]
        }
        
        sio.emit('room_created', room_data, room=sid)
        
        # Notify other participants about the new room
        for participant in room.participants.exclude(id=user.id):
            if participant.id in user_sessions:
                participant_sid = user_sessions[participant.id]['session_id']
                sio.emit('room_invitation', room_data, room=participant_sid)
        
        logger.info(f"Room created by {user.username}: {room.name}")
        
    except Exception as e:
        logger.error(f"Create room error: {str(e)}")
        sio.emit('error', {'message': 'Failed to create room'}, room=sid)

@sio.event
def invite_to_room(sid, data):
    """Invite users to an existing room"""
    try:
        room_id = data.get('room_id')
        user_ids = data.get('user_ids', [])
        
        if not room_id or not user_ids:
            sio.emit('error', {'message': 'Room ID and user IDs required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Verify room access and admin permissions
        try:
            room = ChatRoom.objects.get(id=room_id)
            membership = RoomMembership.objects.get(user=user, room=room)
            if membership.role not in ['admin', 'owner']:
                sio.emit('error', {'message': 'Insufficient permissions'}, room=sid)
                return
        except (ChatRoom.DoesNotExist, RoomMembership.DoesNotExist):
            sio.emit('error', {'message': 'Room not found or access denied'}, room=sid)
            return
            
        # Add new participants
        invited_users = []
        for user_id in user_ids:
            try:
                invite_user = User.objects.get(id=user_id)
                
                # Check if user is already a participant
                if not room.participants.filter(id=user_id).exists():
                    room.participants.add(invite_user)
                    
                    # Create membership
                    RoomMembership.objects.create(
                        user=invite_user,
                        room=room,
                        role='member'
                    )
                    
                    invited_users.append({
                        'user_id': str(invite_user.id),
                        'username': invite_user.username
                    })
                    
                    # Notify the invited user
                    if invite_user.id in user_sessions:
                        invite_sid = user_sessions[invite_user.id]['session_id']
                        sio.emit('room_invitation', {
                            'room_id': str(room.id),
                            'room_name': room.name,
                            'invited_by': user.username
                        }, room=invite_sid)
                        
            except User.DoesNotExist:
                continue
        
        # Notify all room members about new participants
        if invited_users:
            sio.emit('users_invited', {
                'room_id': str(room.id),
                'invited_users': invited_users,
                'invited_by': user.username
            }, room=room_id)
            
        logger.info(f"Users invited to room {room.name} by {user.username}: {len(invited_users)} users")
        
    except Exception as e:
        logger.error(f"Invite to room error: {str(e)}")
        sio.emit('error', {'message': 'Failed to invite users'}, room=sid)

@sio.event
def send_notification(sid, data):
    """Send real-time notification to specific user"""
    try:
        target_user_id = data.get('target_user_id')
        notification_type = data.get('notification_type')
        title = data.get('title', '')
        message = data.get('message', '')
        
        if not target_user_id or not notification_type:
            sio.emit('error', {'message': 'Target user ID and notification type required'}, room=sid)
            return
            
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Find target user's session
        target_session = None
        for user_id, session_data in user_sessions.items():
            if str(user_id) == str(target_user_id):
                target_session = session_data['session_id']
                break
        
        if target_session:
            # Send notification to target user
            notification_data = {
                'type': 'notification',
                'notification_type': notification_type,
                'title': title,
                'message': message,
                'sender_id': str(user.id),
                'sender_username': user.username,
                'timestamp': timezone.now().isoformat()
            }
            
            sio.emit('notification', notification_data, room=target_session)
            logger.info(f"Notification sent from {user.username} to user {target_user_id}: {notification_type}")
        else:
            logger.info(f"Target user {target_user_id} not online - notification will be stored in database")
            
    except Exception as e:
        logger.error(f"Send notification error: {str(e)}")
        sio.emit('error', {'message': 'Failed to send notification'}, room=sid)

@sio.event
def get_user_rooms(sid, data):
    """Get all rooms for the current user"""
    try:
        user = get_user_from_session(sid)
        if not user:
            sio.emit('error', {'message': 'User not authenticated'}, room=sid)
            return
            
        # Get all rooms where user is a participant
        user_rooms = ChatRoom.objects.filter(participants=user, is_active=True).order_by('-updated_at')
        
        rooms_data = []
        for room in user_rooms:
            # Get unread count for this user
            try:
                membership = RoomMembership.objects.get(user=user, room=room)
                unread_count = membership.unread_count
            except RoomMembership.DoesNotExist:
                unread_count = 0
            
            # Get last message
            last_message = room.last_message
            
            # Get other participants
            other_participants = room.participants.exclude(id=user.id)
            
            room_info = {
                'room_id': str(room.id),
                'room_name': room.name,
                'room_type': room.room_type,
                'description': room.description,
                'created_at': room.created_at.isoformat(),
                'updated_at': room.updated_at.isoformat(),
                'unread_count': unread_count,
                'participants': [
                    {
                        'user_id': str(p.id),
                        'username': p.username,
                        'full_name': p.get_full_name()
                    } for p in other_participants
                ],
                'last_message': {
                    'message_id': str(last_message.id),
                    'sender_username': last_message.sender.username,
                    'encrypted_content': last_message.encrypted_content,
                    'message_type': last_message.message_type,
                    'timestamp': last_message.timestamp.isoformat(),
                    'is_edited': last_message.is_edited
                } if last_message else None
            }
            
            rooms_data.append(room_info)
        
        sio.emit('user_rooms', {'rooms': rooms_data}, room=sid)
        logger.info(f"Sent {len(rooms_data)} rooms to user {user.username}")
        
    except Exception as e:
        logger.error(f"Get user rooms error: {str(e)}")
        sio.emit('error', {'message': 'Failed to get user rooms'}, room=sid)

# Create WSGI application
def create_app():
    """Create Socket.IO WSGI application"""
    from django.core.wsgi import get_wsgi_application
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django_app = get_wsgi_application()
    
    # Wrap Django with Socket.IO
    return socketio.WSGIApp(sio, django_app, socketio_path='socket.io')

# Export for use in WSGI
application = create_app()