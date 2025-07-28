from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import TalentProfile, Post
from .serializers import TalentOnboardingSerializer, TalentProfileSerializer, PostSerializer
from mentor.models import MentorProfile
from mentor.serializers import MentorProfileSerializer as MentorProfileDetailSerializer

# Create your views here.

class TalentOnboardingProfileSaveAPIView(generics.GenericAPIView):
    serializer_class = TalentOnboardingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        profile, created = TalentProfile.objects.get_or_create(user=user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=user)
            if not user.onboarding_done:
                user.onboarding_done = True
                user.save(update_fields=["onboarding_done"])
            return Response({
                "success": True,
                "talent_name": user.get_full_name(),
                "profile": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class TalentProfileUpdateAPIView(generics.UpdateAPIView):
    serializer_class = TalentProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return empty profile for schema generation
            return TalentProfile()
        user = self.request.user
        profile, _ = TalentProfile.objects.get_or_create(user=user)
        return profile


class MentorProfileAPIView(generics.RetrieveAPIView):
    """
    Returns the current user's mentor profile
    """
    serializer_class = MentorProfileDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return empty profile for schema generation
            return MentorProfile()
        user = self.request.user
        profile, _ = MentorProfile.objects.get_or_create(user=user)
        return profile


class TalentProfileAPIView(generics.RetrieveAPIView):
    """
    Returns the current user's talent profile
    """
    serializer_class = TalentProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return empty profile for schema generation
            return TalentProfile()
        user = self.request.user
        profile, _ = TalentProfile.objects.get_or_create(user=user)
        return profile


class TalentOwnPostsAPIView(generics.ListAPIView):
    """
    Returns all posts for the logged-in talent user
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return Post.objects.none()
        user = self.request.user
        # Get the talent profile for the current user
        try:
            talent_profile = TalentProfile.objects.get(user=user)
            return Post.objects.filter(talent=talent_profile).select_related('talent__user').prefetch_related('likes', 'views').order_by('-created_at')
        except TalentProfile.DoesNotExist:
            return Post.objects.none()


class PublicFeedAPIView(generics.ListAPIView):
    """
    Public endpoint that returns all posts sorted by creation time (newest first)
    for an Instagram-like feed
    """
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    queryset = Post.objects.select_related('talent__user').prefetch_related('likes', 'views').all()
    ordering = ['-created_at']
