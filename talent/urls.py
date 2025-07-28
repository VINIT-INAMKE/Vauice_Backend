from django.urls import path
from .views import TalentOnboardingProfileSaveAPIView, TalentProfileUpdateAPIView, PublicFeedAPIView, MentorProfileAPIView, TalentProfileAPIView, TalentOwnPostsAPIView

urlpatterns = [
    path('talent/onboarding-profilesave/', TalentOnboardingProfileSaveAPIView.as_view(), name='talent-onboarding-profilesave'),
    path('talent/profile/', TalentProfileUpdateAPIView.as_view(), name='talent-profile-update'),
    path('mentor/profile/', MentorProfileAPIView.as_view(), name='mentor-profile'),
    path('user/talent/profile/', TalentProfileAPIView.as_view(), name='user-talent-profile'),
    path('user/talent/posts/', TalentOwnPostsAPIView.as_view(), name='user-talent-posts'),
    path('feed/', PublicFeedAPIView.as_view(), name='public-feed'),
]