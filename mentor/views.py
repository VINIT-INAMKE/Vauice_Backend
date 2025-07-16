from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import MentorProfile, SelectedTalent, RejectedTalent
from .serializers import MentorOnboardingSerializer, MentorProfileSerializer, SelectedTalentSerializer, RejectedTalentSerializer
from talent.models import TalentProfile
from rest_framework import permissions

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

class MentorSelectedTalentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SelectedTalentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        mentor = MentorProfile.objects.get(user=self.request.user)
        return SelectedTalent.objects.filter(mentor=mentor)

    def perform_create(self, serializer):
        mentor = MentorProfile.objects.get(user=self.request.user)
        serializer.save(mentor=mentor)

class MentorSelectedTalentDeleteAPIView(generics.DestroyAPIView):
    serializer_class = SelectedTalentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        mentor = MentorProfile.objects.get(user=self.request.user)
        return SelectedTalent.objects.filter(mentor=mentor)

class MentorRejectedTalentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RejectedTalentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        mentor = MentorProfile.objects.get(user=self.request.user)
        return RejectedTalent.objects.filter(mentor=mentor)

    def perform_create(self, serializer):
        mentor = MentorProfile.objects.get(user=self.request.user)
        serializer.save(mentor=mentor)

class MentorRejectedTalentDeleteAPIView(generics.DestroyAPIView):
    serializer_class = RejectedTalentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        mentor = MentorProfile.objects.get(user=self.request.user)
        return RejectedTalent.objects.filter(mentor=mentor)
