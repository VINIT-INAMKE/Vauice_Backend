from django.urls import path
from .views import SportsListAPIView, OnboardingStatusAPIView, MentorsWhoSelectedTalentAPIView

urlpatterns = [
    path('core/fetch-sports-list/', SportsListAPIView.as_view(), name='fetch-sports-list'),
    path('core/onboarding-status/<int:user_id>/', OnboardingStatusAPIView.as_view(), name='onboarding-status'),
    path('core/mentors/selected-talent/<int:user_id>/', MentorsWhoSelectedTalentAPIView.as_view(), name='core-mentors-who-selected-talent'),
]  