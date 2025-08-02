"""
Enhanced views for mentor-talent chat workflow
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from mentor.models import MentorProfile
from core.models import MentorTalentSelection
from talent.models import TalentProfile
from .models import ChatRoom, RoomMembership, Message
from .serializers import ChatRoomSerializer, MessageSerializer
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class MentorTalentChatViewSet(viewsets.ViewSet):
    """
    ViewSet for mentor-talent specific chat operations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def mentor_chat_rooms(self, request):
        """
        Get all chat rooms for a mentor with their selected talents
        """
        user = request.user
        
        # Ensure user is a mentor
        if user.user_type != 'mentor':
            return Response(
                {'error': 'Only mentors can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            mentor_profile = user.mentor_profile
        except MentorProfile.DoesNotExist:
            return Response(
                {'error': 'Mentor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all selected talents for this mentor
        selected_talents = MentorTalentSelection.objects.filter(mentor=user)
        talent_users = [st.talent for st in selected_talents]
        
        # Get chat rooms with these talents
        chat_rooms = ChatRoom.objects.filter(
            room_type='private',
            participants=user
        ).filter(
            participants__in=talent_users
        ).distinct().prefetch_related(
            'participants',
            'memberships__user',
            'messages'
        ).order_by('-updated_at')
        
        # Add talent profile info and additional details to each room
        room_data = []
        for room in chat_rooms:
            # Get mentor's membership in this room to get unread count
            try:
                membership = room.memberships.get(user=user)
                unread_count = membership.unread_count
            except RoomMembership.DoesNotExist:
                unread_count = 0
            
            # Get last message if exists
            last_message = room.last_message
            
            room_serializer = ChatRoomSerializer(room)
            room_info = room_serializer.data
            room_info['unread_count'] = unread_count
            
            if last_message:
                # Serialize last message
                last_message_serializer = MessageSerializer(last_message)
                room_info['last_message'] = last_message_serializer.data
            else:
                room_info['last_message'] = None
            
            # Get the talent in this room
            talent_user = room.participants.exclude(id=user.id).first()
            if talent_user and hasattr(talent_user, 'talent_profile'):
                room_info['talent_info'] = {
                    'id': talent_user.id,
                    'username': talent_user.username,
                    'full_name': talent_user.get_full_name(),
                    'selected_sports': talent_user.talent_profile.selected_sports,
                    'experience_years': talent_user.talent_profile.experience_years,
                    'profile_picture': talent_user.talent_profile.profile_picture.url if talent_user.talent_profile.profile_picture else None,
                    'is_verified': talent_user.talent_profile.is_verified
                }
            
            room_data.append(room_info)
        
        return Response(room_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def talent_chat_rooms(self, request):
        """
        Get all chat rooms for a talent with their mentors
        """
        user = request.user
        
        # Ensure user is a talent
        if user.user_type != 'talent':
            return Response(
                {'error': 'Only talents can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            talent_profile = user.talent_profile
        except TalentProfile.DoesNotExist:
            return Response(
                {'error': 'Talent profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all mentors who selected this talent
        selected_by_mentors = MentorTalentSelection.objects.filter(talent=user)
        mentor_users = [st.mentor for st in selected_by_mentors]
        
        # Get chat rooms with these mentors
        chat_rooms = ChatRoom.objects.filter(
            room_type='private',
            participants=user
        ).filter(
            participants__in=mentor_users
        ).distinct().prefetch_related(
            'participants',
            'memberships__user',
            'messages'
        ).order_by('-updated_at')
        
        # Add mentor profile info and additional details to each room
        room_data = []
        for room in chat_rooms:
            # Get talent's membership in this room to get unread count
            try:
                membership = room.memberships.get(user=user)
                unread_count = membership.unread_count
            except RoomMembership.DoesNotExist:
                unread_count = 0
            
            # Get last message if exists
            last_message = room.last_message
            
            room_serializer = ChatRoomSerializer(room)
            room_info = room_serializer.data
            room_info['unread_count'] = unread_count
            
            if last_message:
                # Serialize last message
                last_message_serializer = MessageSerializer(last_message)
                room_info['last_message'] = last_message_serializer.data
            else:
                room_info['last_message'] = None
            
            # Get the mentor in this room
            mentor_user = room.participants.exclude(id=user.id).first()
            if mentor_user and hasattr(mentor_user, 'mentor_profile'):
                room_info['mentor_info'] = {
                    'id': mentor_user.id,
                    'username': mentor_user.username,
                    'full_name': mentor_user.get_full_name(),
                    'selected_sports': mentor_user.mentor_profile.selected_sports,
                    'coaching_experience_years': mentor_user.mentor_profile.coaching_experience_years,
                    'bio': mentor_user.mentor_profile.bio,
                    'location': mentor_user.mentor_profile.location,
                    'is_verified': getattr(mentor_user.mentor_profile, 'is_verified', False)
                }
            
            room_data.append(room_info)
        
        return Response(room_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def create_mentor_talent_chat(self, request):
        """
        Manually create a chat room between mentor and talent
        (Usually this happens automatically via signals when talent is selected)
        """
        user = request.user
        talent_id = request.data.get('talent_id')
        
        if not talent_id:
            return Response(
                {'error': 'talent_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure user is a mentor
        if user.user_type != 'mentor':
            return Response(
                {'error': 'Only mentors can create mentor-talent chats'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            mentor_profile = user.mentor_profile
            talent_user = User.objects.get(id=talent_id, user_type='talent')
            talent_profile = talent_user.talent_profile
        except (MentorProfile.DoesNotExist, User.DoesNotExist, TalentProfile.DoesNotExist):
            return Response(
                {'error': 'Mentor or talent profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if mentor has selected this talent
        if not MentorTalentSelection.objects.filter(mentor=user, talent=talent_user).exists():
            return Response(
                {'error': 'You can only chat with talents you have selected'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if chat room already exists
        existing_room = ChatRoom.objects.filter(
            room_type='private',
            participants=user
        ).filter(
            participants=talent_user
        ).first()
        
        if existing_room:
            return Response(
                ChatRoomSerializer(existing_room).data,
                status=status.HTTP_200_OK
            )
        
        # Create new chat room
        room = ChatRoom.objects.create(
            name=f"Mentor-Talent Chat: {user.get_full_name()} & {talent_user.get_full_name()}",
            room_type='private',
            created_by=user,
            description=f"Private chat between mentor {user.get_full_name()} and talent {talent_user.get_full_name()}"
        )
        
        # Add participants
        room.participants.add(user, talent_user)
        
        # Create memberships
        RoomMembership.objects.create(user=user, room=room, role='member')
        RoomMembership.objects.create(user=talent_user, room=room, role='member')
        
        return Response(
            ChatRoomSerializer(room).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def can_chat_with(self, request):
        """
        Check if current user can chat with another user based on mentor-talent relationship
        """
        other_user_id = request.query_params.get('user_id')
        
        if not other_user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = request.user
        can_chat = False
        reason = ""
        
        # Check mentor-talent relationship
        if user.user_type == 'mentor' and other_user.user_type == 'talent':
            try:
                mentor_profile = user.mentor_profile
                talent_profile = other_user.talent_profile
                
                if MentorTalentSelection.objects.filter(mentor=user, talent=other_user).exists():
                    can_chat = True
                    reason = "Mentor has selected this talent"
                else:
                    reason = "Mentor has not selected this talent"
                    
            except (MentorProfile.DoesNotExist, TalentProfile.DoesNotExist):
                reason = "Profile not found"
                
        elif user.user_type == 'talent' and other_user.user_type == 'mentor':
            try:
                talent_profile = user.talent_profile
                mentor_profile = other_user.mentor_profile
                
                if MentorTalentSelection.objects.filter(mentor=other_user, talent=user).exists():
                    can_chat = True
                    reason = "Talent has been selected by this mentor"
                else:
                    reason = "Talent has not been selected by this mentor"
                    
            except (MentorProfile.DoesNotExist, TalentProfile.DoesNotExist):
                reason = "Profile not found"
        else:
            reason = "Invalid user type combination for mentor-talent chat"
        
        return Response({
            'can_chat': can_chat,
            'reason': reason,
            'user_type': user.user_type,
            'other_user_type': other_user.user_type
        }, status=status.HTTP_200_OK)
