from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework import status
from core.models import MentorTalentSelection
from mentor.models import MentorProfile
from mentor.serializers import MentorProfileSerializer

# Famous and most played sports list as a dict for JSON response
SPORTS_LIST = {
    "football": "Football (Soccer)",
    "cricket": "Cricket",
    "basketball": "Basketball",
    "tennis": "Tennis",
    "volleyball": "Volleyball",
    "table_tennis": "Table Tennis",
    "baseball": "Baseball",
    "golf": "Golf",
    "badminton": "Badminton",
    "rugby": "Rugby",
    "american_football": "American Football",
    "field_hockey": "Field Hockey",
    "ice_hockey": "Ice Hockey",
    "swimming": "Swimming",
    "athletics": "Athletics (Track & Field)",
    "boxing": "Boxing",
    "martial_arts": "Martial Arts (Karate, Taekwondo, Judo, etc.)",
    "cycling": "Cycling",
    "wrestling": "Wrestling",
    "gymnastics": "Gymnastics",
    "handball": "Handball",
    "squash": "Squash",
    "snooker": "Snooker/Billiards",
    "motorsport": "Motorsport (Formula 1, MotoGP, etc.)",
    "esports": "Esports",
    "skateboarding": "Skateboarding",
    "surfing": "Surfing",
    "skiing": "Skiing",
    "snowboarding": "Snowboarding",
    "table_football": "Table Football (Foosball)"
}

class SportsListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"sports": SPORTS_LIST})

class OnboardingStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"onboarding_done": user.onboarding_done})

class MentorsWhoSelectedTalentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Use authenticated user instead of user_id parameter
        talent_user = request.user
        
        # Verify user is a talent
        if talent_user.user_type != 'talent':
            return Response({'error': 'Only talents can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
        
        selections = MentorTalentSelection.objects.filter(talent=talent_user).select_related('mentor__mentor_profile')
        result = []
        for selection in selections:
            mentor_profile = getattr(selection.mentor, 'mentor_profile', None)
            if mentor_profile:
                mentor_data = MentorProfileSerializer(mentor_profile).data
                result.append({
                    'mentor': mentor_data,
                    'selected_at': selection.selected_at
                })
        return Response(result)
