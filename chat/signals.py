"""
Django signals to automatically create chat rooms when mentor selects talent
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from core.models import MentorTalentSelection
from .models import ChatRoom, RoomMembership
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=MentorTalentSelection)
def create_mentor_talent_chat_room(sender, instance, created, **kwargs):
    """
    Automatically create a private chat room when a mentor selects a talent
    """
    if created:  # Only when a new selection is made
        try:
            mentor_user = instance.mentor
            talent_user = instance.talent
            
            # Check if a chat room already exists between these users
            existing_room = ChatRoom.objects.filter(
                room_type='private',
                participants=mentor_user
            ).filter(
                participants=talent_user
            ).first()
            
            if not existing_room:
                # Create new private chat room
                room = ChatRoom.objects.create(
                    name=f"Mentor-Talent Chat: {mentor_user.get_full_name()} & {talent_user.get_full_name()}",
                    room_type='private',
                    created_by=mentor_user,
                    description=f"Private chat between mentor {mentor_user.get_full_name()} and talent {talent_user.get_full_name()}"
                )
                
                # Add both users as participants
                room.participants.add(mentor_user, talent_user)
                
                # Create memberships
                RoomMembership.objects.create(
                    user=mentor_user,
                    room=room,
                    role='member'
                )
                
                RoomMembership.objects.create(
                    user=talent_user,
                    room=room,
                    role='member'
                )
                
                logger.info(f"Created chat room {room.id} for mentor {mentor_user.username} and talent {talent_user.username}")
                
                # Real-time notifications now handled by Socket.io
                # Socket.io will handle new chat room notifications when users connect
                logger.info(f"New chat room notification for talent {talent_user.username} - mentor: {mentor_user.get_full_name()}")
            else:
                logger.info(f"Chat room already exists between mentor {mentor_user.username} and talent {talent_user.username}")
                
        except Exception as e:
            logger.error(f"Error creating mentor-talent chat room: {str(e)}")
