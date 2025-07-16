from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import TalentProfile
from .serializers import TalentOnboardingSerializer, TalentProfileSerializer

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
        user = self.request.user
        profile, _ = TalentProfile.objects.get_or_create(user=user)
        return profile
