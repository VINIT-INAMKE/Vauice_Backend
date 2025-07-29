from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import MentorProfile, SelectedTalent, RejectedTalent
from .serializers import (
    MentorOnboardingSerializer, MentorProfileSerializer, SelectedTalentSerializer, RejectedTalentSerializer,
    TalentWithPostsSerializer, CountSerializer, SelectedTalentWithPostsSerializer, RejectedTalentWithPostsSerializer
)
from talent.models import TalentProfile, Post, PostLike, PostView
from chat.models import ChatRoom
from talent.serializers import TalentProfileSerializer, PostSerializer, PostLikeSerializer, PostViewSerializer
from notifications.utils import send_mentor_selected_talent_notification, send_talent_rejected_notification
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from userauths.models import User

# Create your views here.

class MentorOnboardingProfileSaveAPIView(generics.GenericAPIView):
    serializer_class = MentorOnboardingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        profile, created = MentorProfile.objects.get_or_create(user=user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=user)
            if not user.onboarding_done:
                user.onboarding_done = True
                user.save(update_fields=["onboarding_done"])
            return Response({
                "success": True,
                "mentor_name": user.get_full_name(),
                "profile": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class MentorProfileUpdateAPIView(generics.UpdateAPIView):
    serializer_class = MentorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        profile, _ = MentorProfile.objects.get_or_create(user=user)
        return profile

class AddSelectedTalentAPIView(generics.CreateAPIView):
    serializer_class = SelectedTalentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        talent_id = request.data.get('talent_id')
        if not user_id or not talent_id:
            return Response({'error': 'user_id and talent_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            mentor = MentorProfile.objects.get(id=user_id)
            talent = TalentProfile.objects.get(id=talent_id)
        except (MentorProfile.DoesNotExist, TalentProfile.DoesNotExist):
            return Response({'error': 'Mentor or Talent not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        obj, created = SelectedTalent.objects.get_or_create(mentor=mentor, talent=talent)
        
        # Create chat room when talent is selected (only if newly created)
        if created:
            self._create_mentor_talent_chat_room(mentor, talent)
            # Send notification to talent
            try:
                send_mentor_selected_talent_notification(mentor, talent)
            except Exception as e:
                # Log error but don't fail the talent selection
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error sending mentor selected talent notification: {str(e)}")
        
        # Get recent posts for the talent
        posts = Post.objects.filter(talent=talent)
        posts_data = PostSerializer(posts, many=True).data
        
        # Add chat room info to response
        chat_room = self._get_existing_chat_room(mentor.user, talent.user)
        chat_room_id = str(chat_room.id) if chat_room else None
        can_chat = bool(chat_room)
        
        # Create response data with talent object and posts
        response_data = {
            'id': obj.id,
            'talent': TalentProfileSerializer(talent).data,
            'selected_at': obj.selected_at,
            'chat_room_id': chat_room_id,
            'can_chat': can_chat,
            'posts': posts_data
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    def _create_mentor_talent_chat_room(self, mentor_profile, talent_profile):
        """Create a private chat room between mentor and talent"""
        try:
            from chat.models import ChatRoom, RoomMembership
            
            mentor_user = mentor_profile.user
            talent_user = talent_profile.user
            
            # Check if chat room already exists
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
                
                # Optional: Send notification to talent
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f'user_{talent_user.id}',
                            {
                                'type': 'notification',
                                'notification_type': 'new_mentor_chat',
                                'room_id': str(room.id),
                                'mentor_name': mentor_user.get_full_name(),
                                'message': f'You can now chat with your mentor {mentor_user.get_full_name()}'
                            }
                        )
                except ImportError:
                    pass  # Channels not available
                    
                return room
            return existing_room
            
        except ImportError:
            # Chat app not available
            pass
        except Exception as e:
            # Log error but don't fail the talent selection
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating mentor-talent chat room: {str(e)}")
    
    def _get_existing_chat_room(self, mentor_user, talent_user):
        """Get existing chat room between mentor and talent"""
        try:
            from chat.models import ChatRoom
            
            return ChatRoom.objects.filter(
                room_type='private',
                participants=mentor_user
            ).filter(
                participants=talent_user
            ).first()
            
        except ImportError:
            return None

class ListSelectedTalentsAPIView(generics.ListAPIView):
    serializer_class = SelectedTalentWithPostsSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('user_id', openapi.IN_QUERY, description="Mentor profile ID", type=openapi.TYPE_INTEGER, required=True)
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if not user_id:
            self.error = {'error': 'user_id query parameter is required.'}
            return TalentProfile.objects.none()
        try:
            mentor = MentorProfile.objects.get(id=user_id)
        except MentorProfile.DoesNotExist:
            self.error = {'error': 'Mentor profile not found.'}
            return TalentProfile.objects.none()
        # Get all selected talents with their related data
        return SelectedTalent.objects.filter(mentor=mentor).select_related('talent')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if hasattr(self, 'error'):
            return Response(self.error, status=status.HTTP_400_BAD_REQUEST)
        
        result = []
        for selected_talent in queryset:
            talent = selected_talent.talent
            # Get recent posts for the talent
            posts = Post.objects.filter(talent=talent)
            posts_data = PostSerializer(posts, many=True).data
            
            # Get chat room info
            chat_room_id = None
            can_chat = False
            try:
                chat_room = ChatRoom.objects.filter(
                    room_type='private',
                    participants=selected_talent.mentor.user
                ).filter(
                    participants=talent.user
                ).first()
                if chat_room:
                    chat_room_id = str(chat_room.id)
                    can_chat = True
            except ChatRoom.DoesNotExist:
                pass
            
            result.append({
                'talent': TalentProfileSerializer(talent).data,
                'selected_at': selected_talent.selected_at,
                'chat_room_id': chat_room_id,
                'can_chat': can_chat,
                'posts': posts_data
            })
        
        serializer = self.get_serializer(result, many=True)
        return Response(serializer.data)

class AddRejectedTalentAPIView(generics.CreateAPIView):
    serializer_class = RejectedTalentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        talent_id = request.data.get('talent_id')
        if not user_id or not talent_id:
            return Response({'error': 'user_id and talent_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            mentor = MentorProfile.objects.get(id=user_id)
            talent = TalentProfile.objects.get(id=talent_id)
        except (MentorProfile.DoesNotExist, TalentProfile.DoesNotExist):
            return Response({'error': 'Mentor or Talent not found.'}, status=status.HTTP_404_NOT_FOUND)
        obj, created = RejectedTalent.objects.get_or_create(mentor=mentor, talent=talent)
        
        # Send notification to talent when rejected (only if newly created)
        if created:
            try:
                send_talent_rejected_notification(mentor, talent)
            except Exception as e:
                # Log error but don't fail the talent rejection
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error sending talent rejected notification: {str(e)}")
        
        # Get recent posts for the talent
        posts = Post.objects.filter(talent=talent)
        posts_data = PostSerializer(posts, many=True).data
        
        # Create response data with talent object and posts
        response_data = {
            'id': obj.id,
            'talent': TalentProfileSerializer(talent).data,
            'rejected_at': obj.rejected_at,
            'posts': posts_data
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ListRejectedTalentsAPIView(generics.ListAPIView):
    serializer_class = RejectedTalentWithPostsSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('user_id', openapi.IN_QUERY, description="Mentor profile ID", type=openapi.TYPE_INTEGER, required=True)
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if not user_id:
            self.error = {'error': 'user_id query parameter is required.'}
            return TalentProfile.objects.none()
        try:
            mentor = MentorProfile.objects.get(id=user_id)
        except MentorProfile.DoesNotExist:
            self.error = {'error': 'Mentor profile not found.'}
            return TalentProfile.objects.none()
        # Get all rejected talents with their related data
        return RejectedTalent.objects.filter(mentor=mentor).select_related('talent')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if hasattr(self, 'error'):
            return Response(self.error, status=status.HTTP_400_BAD_REQUEST)
        
        result = []
        for rejected_talent in queryset:
            talent = rejected_talent.talent
            # Get recent posts for the talent
            posts = Post.objects.filter(talent=talent)
            posts_data = PostSerializer(posts, many=True).data
            
            result.append({
                'talent': TalentProfileSerializer(talent).data,
                'rejected_at': rejected_talent.rejected_at,
                'posts': posts_data
            })
        
        serializer = self.get_serializer(result, many=True)
        return Response(serializer.data)



class AddPostAPIView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [AllowAny]

class DeletePostAPIView(generics.DestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    queryset = Post.objects.all()
    lookup_field = 'pk'

class AddLikeAPIView(generics.CreateAPIView):
    serializer_class = PostLikeSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        post_id = request.data.get('post')
        user_id = request.data.get('user')
        if not post_id or not user_id:
            return Response({'error': 'post and user are required.'}, status=status.HTTP_400_BAD_REQUEST)
        # Enforce one like per user per post
        like, created = PostLike.objects.get_or_create(post_id=post_id, user_id=user_id)
        serializer = self.get_serializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class UnlikeAPIView(generics.DestroyAPIView):
    serializer_class = PostLikeSerializer
    permission_classes = [AllowAny]
    def get_object(self):
        post_id = self.request.data.get('post') or self.request.query_params.get('post')
        user_id = self.request.data.get('user') or self.request.query_params.get('user')
        return PostLike.objects.get(post_id=post_id, user_id=user_id)

class AddViewAPIView(generics.CreateAPIView):
    serializer_class = PostViewSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        post_id = request.data.get('post')
        user_id = request.data.get('user')
        if not post_id or not user_id:
            return Response({'error': 'post and user are required.'}, status=status.HTTP_400_BAD_REQUEST)
        # Enforce one view per user per post
        view, created = PostView.objects.get_or_create(post_id=post_id, user_id=user_id)
        serializer = self.get_serializer(view)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ListAvailableTalentsWithPostsAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TalentWithPostsSerializer

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('user_id', openapi.IN_QUERY, description="Mentor profile ID", type=openapi.TYPE_INTEGER, required=True)
    ])
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            mentor = MentorProfile.objects.get(user__id=user_id)
        except MentorProfile.DoesNotExist:
            return Response({'error': 'Mentor profile not found.'}, status=status.HTTP_400_BAD_REQUEST)
        selected_ids = SelectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        rejected_ids = RejectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        available_talents = TalentProfile.objects.exclude(id__in=list(selected_ids) + list(rejected_ids))
        serializer = self.get_serializer(available_talents, many=True)
        return Response(serializer.data)

class PostLikesCountAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CountSerializer

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('post_id', openapi.IN_QUERY, description="Post ID", type=openapi.TYPE_INTEGER, required=True)
    ])
    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get('post_id')
        if not post_id:
            return Response({'error': 'post_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = {'post_id': int(post_id), 'count': post.likes.count()}
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class PostViewsCountAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CountSerializer

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('post_id', openapi.IN_QUERY, description="Post ID", type=openapi.TYPE_INTEGER, required=True)
    ])
    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get('post_id')
        if not post_id:
            return Response({'error': 'post_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = {'post_id': int(post_id), 'count': post.views.count()}
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class MentorsWhoSelectedTalentAPIView(APIView):
    """
    Returns all mentor profiles (with selected_at) who have selected the given talent (by user_id)
    """
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            talent_profile = TalentProfile.objects.get(user__id=user_id)
        except TalentProfile.DoesNotExist:
            return Response({'detail': 'Talent profile not found'}, status=status.HTTP_404_NOT_FOUND)
        selected_qs = SelectedTalent.objects.filter(talent=talent_profile).select_related('mentor__user')
        result = []
        for selected in selected_qs:
            mentor_data = MentorProfileSerializer(selected.mentor).data
            result.append({
                'mentor': mentor_data,
                'selected_at': selected.selected_at
            })
        return Response(result)
