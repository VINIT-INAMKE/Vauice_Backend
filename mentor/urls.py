from django.urls import path
from .views import (
    MentorOnboardingProfileSaveAPIView,
    MentorProfileUpdateAPIView,
    AddSelectedTalentAPIView,
    ListSelectedTalentsAPIView,
    AddRejectedTalentAPIView,
    ListRejectedTalentsAPIView,
    ListAvailableTalentsAPIView,
    AddPostAPIView,
    DeletePostAPIView,
    AddLikeAPIView,
    UnlikeAPIView,
    AddViewAPIView,
    ListAvailableTalentsWithPostsAPIView,
    PostLikesCountAPIView,
    PostViewsCountAPIView,
)

urlpatterns = [
    path('mentor/onboarding-profilesave/', MentorOnboardingProfileSaveAPIView.as_view(), name='mentor-onboarding-profilesave'),
    path('mentor/profile/', MentorProfileUpdateAPIView.as_view(), name='mentor-profile-update'),
    # Selected Talents
    path('mentor/selected-talents/add/', AddSelectedTalentAPIView.as_view(), name='mentor-selected-talents-add'),
    path('mentor/selected-talents/', ListSelectedTalentsAPIView.as_view(), name='mentor-selected-talents-list'),
    # Rejected Talents
    path('mentor/rejected-talents/add/', AddRejectedTalentAPIView.as_view(), name='mentor-rejected-talents-add'),
    path('mentor/rejected-talents/', ListRejectedTalentsAPIView.as_view(), name='mentor-rejected-talents-list'),
    # Available Talents
    path('mentor/available-talents/', ListAvailableTalentsAPIView.as_view(), name='mentor-available-talents-list'),
    # Post APIs
    path('posts/add/', AddPostAPIView.as_view(), name='add-post'),
    path('posts/<int:pk>/delete/', DeletePostAPIView.as_view(), name='delete-post'),
    path('posts/like/', AddLikeAPIView.as_view(), name='add-like'),
    path('posts/unlike/', UnlikeAPIView.as_view(), name='unlike-post'),
    path('posts/view/', AddViewAPIView.as_view(), name='add-view'),
    path('mentor/available-talents-with-posts/', ListAvailableTalentsWithPostsAPIView.as_view(), name='mentor-available-talents-with-posts'),
    path('posts/likes-count/', PostLikesCountAPIView.as_view(), name='post-likes-count'),
    path('posts/views-count/', PostViewsCountAPIView.as_view(), name='post-views-count'),
] 