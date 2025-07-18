from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import MentorProfile, SelectedTalent, RejectedTalent
from .serializers import (
    MentorOnboardingSerializer, MentorProfileSerializer, SelectedTalentSerializer, RejectedTalentSerializer,
    TalentWithPostsSerializer, CountSerializer
)
from talent.models import TalentProfile, Post, PostLike, PostView
from talent.serializers import TalentProfileSerializer, PostSerializer, PostLikeSerializer, PostViewSerializer
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ListSelectedTalentsAPIView(generics.ListAPIView):
    serializer_class = TalentProfileSerializer
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
        # Get all talent profiles from selected talents
        selected_talents = SelectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        return TalentProfile.objects.filter(id__in=selected_talents)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if hasattr(self, 'error'):
            return Response(self.error, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(queryset, many=True)
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
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ListRejectedTalentsAPIView(generics.ListAPIView):
    serializer_class = TalentProfileSerializer
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
        # Get all talent profiles from rejected talents
        rejected_talents = RejectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        return TalentProfile.objects.filter(id__in=rejected_talents)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if hasattr(self, 'error'):
            return Response(self.error, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ListAvailableTalentsAPIView(generics.ListAPIView):
    serializer_class = TalentProfileSerializer
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
        selected_ids = SelectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        rejected_ids = RejectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        return TalentProfile.objects.exclude(id__in=list(selected_ids) + list(rejected_ids))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if hasattr(self, 'error'):
            return Response(self.error, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(queryset, many=True)
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
            mentor = MentorProfile.objects.get(id=user_id)
        except MentorProfile.DoesNotExist:
            return Response({'error': 'Mentor profile not found.'}, status=status.HTTP_400_BAD_REQUEST)
        selected_ids = SelectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        rejected_ids = RejectedTalent.objects.filter(mentor=mentor).values_list('talent', flat=True)
        available_talents = TalentProfile.objects.exclude(id__in=list(selected_ids) + list(rejected_ids))
        result = []
        for talent in available_talents:
            posts = Post.objects.filter(talent=talent)
            posts_data = PostSerializer(posts, many=True).data
            result.append({
                'talent': talent.id,
                'posts': posts_data
            })
        serializer = self.get_serializer(result, many=True)
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
