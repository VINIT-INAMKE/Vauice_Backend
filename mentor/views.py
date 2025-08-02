from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import MentorProfile
from core.models import TalentPool, MentorTalentSelection, MentorTalentRejection
from core.serializers import MentorTalentSelectionSerializer, MentorTalentRejectionSerializer, MentorTalentSelectionCreateSerializer, MentorTalentRejectionCreateSerializer
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
    serializer_class = MentorTalentSelectionCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Use authenticated user as mentor
        mentor_user = request.user
        
        # Verify user is a mentor
        if mentor_user.user_type != 'mentor':
            return Response({'error': 'Only mentors can select talents.'}, status=status.HTTP_403_FORBIDDEN)
        
        talent_id = request.data.get('talent_id')
        if not talent_id:
            return Response({'error': 'talent_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            talent_user = User.objects.get(id=talent_id, user_type='talent')
        except User.DoesNotExist:
            return Response({'error': 'Talent user not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create serializer with the user data
        serializer = self.get_serializer(data={'mentor': mentor_user.id, 'talent': talent_user.id})
        if serializer.is_valid():
            # Check if this is a new selection
            existing = MentorTalentSelection.objects.filter(mentor=mentor_user, talent=talent_user).exists()
            created = not existing
            
            # Create the selection
            selection = serializer.save()
            
            # Handle side effects for new selections
            if created:
                # Get profiles for notifications and chat room
                try:
                    talent_profile = talent_user.talent_profile
                    mentor_profile = mentor_user.mentor_profile
                    
                    # Create chat room
                    self._create_mentor_talent_chat_room(mentor_profile, talent_profile)
                    
                    # Send notification
                    try:
                        send_mentor_selected_talent_notification(mentor_profile, talent_profile)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error sending mentor selected talent notification: {str(e)}")
                        
                except (TalentProfile.DoesNotExist, MentorProfile.DoesNotExist):
                    pass  # Continue without notifications if profile doesn't exist
            
            # Return full selection data using the detailed serializer
            response_serializer = MentorTalentSelectionSerializer(selection)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
                
                # Real-time notifications now handled by Socket.io
                # Socket.io will handle mentor-talent chat notifications
                logger.info(f"Chat room created between mentor {mentor_user.username} and talent {talent_user.username}")
                
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
    serializer_class = MentorTalentSelectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Use authenticated user
        mentor_user = self.request.user
        
        # Verify user is a mentor
        if mentor_user.user_type != 'mentor':
            return MentorTalentSelection.objects.none()
        
        # Get all selected talents with their related data
        return MentorTalentSelection.objects.filter(mentor=mentor_user).select_related(
            'talent__talent_profile', 'mentor__mentor_profile'
        ).prefetch_related('talent__talent_profile__posts')

    def list(self, request, *args, **kwargs):
        # Verify user is a mentor
        if request.user.user_type != 'mentor':
            return Response({'error': 'Only mentors can access selected talents.'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().list(request, *args, **kwargs)

class AddRejectedTalentAPIView(generics.CreateAPIView):
    serializer_class = MentorTalentRejectionCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Use authenticated user as mentor
        mentor_user = request.user
        
        # Verify user is a mentor
        if mentor_user.user_type != 'mentor':
            return Response({'error': 'Only mentors can reject talents.'}, status=status.HTTP_403_FORBIDDEN)
        
        talent_id = request.data.get('talent_id')
        if not talent_id:
            return Response({'error': 'talent_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            talent_user = User.objects.get(id=talent_id, user_type='talent')
        except User.DoesNotExist:
            return Response({'error': 'Talent user not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create serializer with the user data
        serializer = self.get_serializer(data={'mentor': mentor_user.id, 'talent': talent_user.id})
        if serializer.is_valid():
            # Check if this is a new rejection
            existing = MentorTalentRejection.objects.filter(mentor=mentor_user, talent=talent_user).exists()
            created = not existing
            
            # Create the rejection
            rejection = serializer.save()
            
            # Handle side effects for new rejections
            if created:
                # Get profiles for notifications
                try:
                    talent_profile = talent_user.talent_profile
                    mentor_profile = mentor_user.mentor_profile
                    
                    # Send notification
                    try:
                        send_talent_rejected_notification(mentor_profile, talent_profile)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error sending talent rejected notification: {str(e)}")
                        
                except (TalentProfile.DoesNotExist, MentorProfile.DoesNotExist):
                    pass  # Continue without notifications if profile doesn't exist
            
            # Return full rejection data using the detailed serializer
            response_serializer = MentorTalentRejectionSerializer(rejection)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListRejectedTalentsAPIView(generics.ListAPIView):
    serializer_class = MentorTalentRejectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Use authenticated user
        mentor_user = self.request.user
        
        # Verify user is a mentor
        if mentor_user.user_type != 'mentor':
            return MentorTalentRejection.objects.none()
        
        # Get all rejected talents with their related data
        return MentorTalentRejection.objects.filter(mentor=mentor_user).select_related(
            'talent__talent_profile', 'mentor__mentor_profile'
        ).prefetch_related('talent__talent_profile__posts')

    def list(self, request, *args, **kwargs):
        # Verify user is a mentor
        if request.user.user_type != 'mentor':
            return Response({'error': 'Only mentors can access rejected talents.'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().list(request, *args, **kwargs)



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
    permission_classes = [IsAuthenticated]
    serializer_class = TalentWithPostsSerializer

    def get(self, request, *args, **kwargs):
        # Use authenticated user instead of query parameter
        mentor_user = request.user
        
        # Verify user is a mentor
        if mentor_user.user_type != 'mentor':
            return Response({'error': 'Only mentors can access talent pool.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get talent User IDs from the authenticated mentor's TalentPool
        talent_user_ids = TalentPool.objects.filter(mentor=mentor_user).values_list('talent_id', flat=True)
        
        # Get TalentProfiles with related data for those users
        available_talents = TalentProfile.objects.filter(
            user_id__in=talent_user_ids
        ).select_related('user').prefetch_related('posts')
        
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

