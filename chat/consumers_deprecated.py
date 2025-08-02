import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatRoom, Message, UserPresence, MessageStatus, RoomMembership
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from notifications.utils import send_new_message_notification
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat messaging"""
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = None
        
        # Authenticate user from token
        await self.authenticate_user()
        
        if self.user and not isinstance(self.user, AnonymousUser):
            # Check if user has access to this room
            has_access = await self.check_room_access()
            
            if has_access:
                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                
                await self.accept()
                
                # Set user as online and in this room
                await self.set_user_online()
                
                # Notify others that user joined
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_joined',
                        'user_id': str(self.user.id),
                        'username': self.user.username,
                    }
                )
                
                logger.info(f"User {self.user.username} connected to room {self.room_id}")
            else:
                await self.close(code=4003)  # Forbidden
        else:
            await self.close(code=4001)  # Unauthorized

    async def disconnect(self, close_code):
        if self.user and hasattr(self, 'room_group_name'):
            # Set user as offline
            await self.set_user_offline()
            
            # Notify others that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.username} disconnected from room {self.room_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing_start':
                await self.handle_typing_start()
            elif message_type == 'typing_stop':
                await self.handle_typing_stop()
            elif message_type == 'message_read':
                await self.handle_message_read(data)
            elif message_type == 'message_edit':
                await self.handle_message_edit(data)
            elif message_type == 'message_delete':
                await self.handle_message_delete(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def handle_chat_message(self, data):
        """Handle incoming chat messages"""
        encrypted_content = data.get('encrypted_content')
        content_hash = data.get('content_hash')
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to')
        
        if not encrypted_content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message content is required'
            }))
            return
        
        # Save message to database
        message = await self.save_message(
            encrypted_content, content_hash, message_type, reply_to_id
        )
        
        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': await self.serialize_message(message)
                }
            )
            
            # Update message status for all room participants
            await self.update_message_status(message, 'delivered')
            
            # Send notification to recipient
            try:
                await database_sync_to_async(send_new_message_notification)(message)
            except Exception as e:
                logger.error(f"Error sending new message notification: {str(e)}")

    async def handle_typing_start(self):
        """Handle typing indicator start"""
        await self.set_typing_status(True)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'is_typing': True
            }
        )

    async def handle_typing_stop(self):
        """Handle typing indicator stop"""
        await self.set_typing_status(False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'is_typing': False
            }
        )

    async def handle_message_read(self, data):
        """Handle message read status"""
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_as_read(message_id)

    async def handle_message_edit(self, data):
        """Handle message editing"""
        message_id = data.get('message_id')
        new_encrypted_content = data.get('encrypted_content')
        new_content_hash = data.get('content_hash')
        
        if message_id and new_encrypted_content:
            message = await self.edit_message(message_id, new_encrypted_content, new_content_hash)
            if message:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_edited',
                        'message': await self.serialize_message(message)
                    }
                )

    async def handle_message_delete(self, data):
        """Handle message deletion"""
        message_id = data.get('message_id')
        if message_id:
            success = await self.delete_message(message_id)
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id,
                        'deleted_by': str(self.user.id)
                    }
                )

    # WebSocket event handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps(event))

    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        if event['user_id'] != str(self.user.id):  # Don't send to self
            await self.send(text_data=json.dumps(event))

    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        if event['user_id'] != str(self.user.id):  # Don't send to self
            await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        if event['user_id'] != str(self.user.id):  # Don't send to self
            await self.send(text_data=json.dumps(event))

    async def message_edited(self, event):
        """Send message edited notification to WebSocket"""
        await self.send(text_data=json.dumps(event))

    async def message_deleted(self, event):
        """Send message deleted notification to WebSocket"""
        await self.send(text_data=json.dumps(event))

    # Database operations
    @database_sync_to_async
    def authenticate_user(self):
        """Authenticate user from WebSocket headers"""
        try:
            # Get token from query string or headers
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            if token:
                UntypedToken(token)  # Validate token
                from rest_framework_simplejwt.authentication import JWTAuthentication
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                self.user = jwt_auth.get_user(validated_token)
            else:
                self.user = AnonymousUser()
                
        except (InvalidToken, TokenError, Exception) as e:
            logger.error(f"Authentication error: {str(e)}")
            self.user = AnonymousUser()

    @database_sync_to_async
    def check_room_access(self):
        """Check if user has access to the chat room"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, encrypted_content, content_hash, message_type, reply_to_id):
        """Save message to database"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            reply_to = None
            
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(id=reply_to_id, room=room)
                except Message.DoesNotExist:
                    pass
            
            message = Message.objects.create(
                room=room,
                sender=self.user,
                encrypted_content=encrypted_content,
                content_hash=content_hash,
                message_type=message_type,
                reply_to=reply_to
            )
            
            # Update room's updated_at timestamp
            room.updated_at = timezone.now()
            room.save()
            
            return message
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for WebSocket transmission"""
        return {
            'type': 'chat_message',
            'message_id': str(message.id),
            'room_id': str(message.room.id),
            'sender_id': str(message.sender.id),
            'sender_username': message.sender.username,
            'encrypted_content': message.encrypted_content,
            'content_hash': message.content_hash,
            'message_type': message.message_type,
            'timestamp': message.timestamp.isoformat(),
            'is_edited': message.is_edited,
            'reply_to': str(message.reply_to.id) if message.reply_to else None,
        }

    @database_sync_to_async
    def set_user_online(self):
        """Set user as online"""
        try:
            presence, created = UserPresence.objects.get_or_create(user=self.user)
            presence.set_online()
        except Exception as e:
            logger.error(f"Error setting user online: {str(e)}")

    @database_sync_to_async
    def set_user_offline(self):
        """Set user as offline"""
        try:
            presence = UserPresence.objects.get(user=self.user)
            presence.set_offline()
        except UserPresence.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error setting user offline: {str(e)}")

    @database_sync_to_async
    def set_typing_status(self, is_typing):
        """Set user typing status"""
        try:
            presence, created = UserPresence.objects.get_or_create(user=self.user)
            if is_typing:
                room = ChatRoom.objects.get(id=self.room_id)
                presence.start_typing(room)
            else:
                presence.stop_typing()
        except Exception as e:
            logger.error(f"Error setting typing status: {str(e)}")

    @database_sync_to_async
    def update_message_status(self, message, status):
        """Update message status for room participants"""
        try:
            room_participants = message.room.participants.exclude(id=self.user.id)
            for participant in room_participants:
                MessageStatus.objects.update_or_create(
                    message=message,
                    user=participant,
                    defaults={'status': status}
                )
        except Exception as e:
            logger.error(f"Error updating message status: {str(e)}")

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark message as read by current user"""
        try:
            message = Message.objects.get(id=message_id)
            MessageStatus.objects.update_or_create(
                message=message,
                user=self.user,
                defaults={'status': 'read'}
            )
        except Message.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")

    @database_sync_to_async
    def edit_message(self, message_id, new_encrypted_content, new_content_hash):
        """Edit a message"""
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.user,
                room__id=self.room_id
            )
            message.encrypted_content = new_encrypted_content
            message.content_hash = new_content_hash
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save()
            return message
        except Message.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error editing message: {str(e)}")
            return None

    @database_sync_to_async
    def delete_message(self, message_id):
        """Delete a message (soft delete)"""
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.user,
                room__id=self.room_id
            )
            message.soft_delete()
            return True
        except Message.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return False


class PresenceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for user presence and global notifications"""
    
    async def connect(self):
        self.user = None
        await self.authenticate_user()
        
        if self.user and not isinstance(self.user, AnonymousUser):
            self.user_group_name = f'user_{self.user.id}'
            
            # Join user's personal group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            await self.accept()
            await self.set_user_online()
            
            logger.info(f"User {self.user.username} connected to presence")
        else:
            await self.close(code=4001)  # Unauthorized

    async def disconnect(self, close_code):
        if self.user and hasattr(self, 'user_group_name'):
            await self.set_user_offline()
            
            # Leave user's personal group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.username} disconnected from presence")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                await self.handle_heartbeat()
                
        except json.JSONDecodeError:
            pass  # Ignore invalid JSON
        except Exception as e:
            logger.error(f"Error in presence receive: {str(e)}")

    async def handle_heartbeat(self):
        """Handle heartbeat to keep user online"""
        await self.set_user_online()
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_ack',
            'timestamp': timezone.now().isoformat()
        }))

    # WebSocket event handlers
    async def notification(self, event):
        """Send notification to user"""
        await self.send(text_data=json.dumps(event))

    # Database operations
    @database_sync_to_async
    def authenticate_user(self):
        """Authenticate user from WebSocket headers"""
        try:
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            if token:
                UntypedToken(token)  # Validate token
                from rest_framework_simplejwt.authentication import JWTAuthentication
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                self.user = jwt_auth.get_user(validated_token)
            else:
                self.user = AnonymousUser()
                
        except (InvalidToken, TokenError, Exception) as e:
            logger.error(f"Presence authentication error: {str(e)}")
            self.user = AnonymousUser()

    @database_sync_to_async
    def set_user_online(self):
        """Set user as online"""
        try:
            presence, created = UserPresence.objects.get_or_create(user=self.user)
            presence.set_online()
        except Exception as e:
            logger.error(f"Error setting user online in presence: {str(e)}")

    @database_sync_to_async
    def set_user_offline(self):
        """Set user as offline"""
        try:
            presence = UserPresence.objects.get(user=self.user)
            presence.set_offline()
        except UserPresence.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error setting user offline in presence: {str(e)}")
