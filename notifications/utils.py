from .models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

def send_notification(recipient, sender=None, notification_type=None, title='', message_text='', 
                     talent=None, mentor=None, chat_room=None, message_obj=None):
    """
    Create a notification and send it via WebSocket if the recipient is online
    """
    # Create the notification in the database
    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message_text=message_text,
        talent=talent,
        mentor=mentor,
        chat_room=chat_room,
        message=message_obj
    )
    
    # Send WebSocket notification if recipient is online
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'user_{recipient.id}',
                {
                    'type': 'notification',
                    'notification_id': notification.id,
                    'notification_type': notification_type,
                    'title': title,
                    'message': message_text,
                    'created_at': notification.created_at.isoformat()
                }
            )
    except Exception as e:
        # Log error but don't fail the notification creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending WebSocket notification: {str(e)}")
    
    return notification

def send_mentor_selected_talent_notification(mentor, talent):
    """
    Send notification to talent when selected by mentor
    """
    title = f"New Mentor Selection"
    message = f"{mentor.user.get_full_name()} has selected you as their talent!"
    
    return send_notification(
        recipient=talent.user,
        sender=mentor.user,
        notification_type='mentor_selected',
        title=title,
        message_text=message,
        talent=talent,
        mentor=mentor
    )

def send_talent_rejected_notification(mentor, talent):
    """
    Send notification to talent when rejected by mentor
    """
    title = f"Application Status Update"
    message = f"{mentor.user.get_full_name()} has reviewed your application."
    
    return send_notification(
        recipient=talent.user,
        sender=mentor.user,
        notification_type='talent_rejected',
        title=title,
        message_text=message,
        talent=talent,
        mentor=mentor
    )

def send_new_message_notification(message_obj):
    """
    Send notification to recipient when they receive a new message
    """
    # Determine recipient (the other participant in the chat)
    chat_room = message_obj.room
    sender = message_obj.sender
    
    # Find the recipient (the other user in the chat room)
    recipient_membership = chat_room.memberships.exclude(user=sender).first()
    if not recipient_membership:
        return None
    
    recipient = recipient_membership.user
    
    title = f"New Message from {sender.get_full_name()}"
    message = message_obj.content[:100] + "..." if len(message_obj.content) > 100 else message_obj.content
    
    return send_notification(
        recipient=recipient,
        sender=sender,
        notification_type='new_message',
        title=title,
        message_text=message,
        chat_room=chat_room,
        message_obj=message_obj
    )

def send_chat_room_created_notification(mentor, talent, chat_room):
    """
    Send notification when a chat room is created between mentor and talent
    """
    # Notify talent
    title = f"Chat Room Created"
    message = f"You can now chat with your mentor {mentor.user.get_full_name()}"
    
    return send_notification(
        recipient=talent.user,
        sender=mentor.user,
        notification_type='chat_room_created',
        title=title,
        message_text=message,
        talent=talent,
        mentor=mentor,
        chat_room=chat_room
    )
