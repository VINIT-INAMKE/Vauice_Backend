from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .mentor_talent_views import MentorTalentChatViewSet

router = DefaultRouter()
router.register(r'rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'encryption-keys', views.EncryptionKeyViewSet, basename='encryptionkey')
router.register(r'users/search', views.UserSearchViewSet, basename='usersearch')
router.register(r'files', views.FileUploadViewSet, basename='fileupload')
router.register(r'presence', views.UserPresenceViewSet, basename='userpresence')
router.register(r'mentor-talent', MentorTalentChatViewSet, basename='mentortalentchat')

urlpatterns = [
    path('', include(router.urls)),
]
