from django.urls import path, include
from . import views
from .mentor_talent_views import MentorTalentChatViewSet
from rest_framework.routers import DefaultRouter

# Keep the mentor-talent chat as a ViewSet since it's already working
router = DefaultRouter()
router.register(r'mentor-talent', MentorTalentChatViewSet, basename='mentortalentchat')

urlpatterns = [
    # Chat rooms
    path('rooms/', views.ChatRoomListView.as_view(), name='chatroom-list'),
    path('rooms/<uuid:pk>/', views.ChatRoomDetailView.as_view(), name='chatroom-detail'),
    path('rooms/<uuid:pk>/invite/', views.ChatRoomInviteView.as_view(), name='chatroom-invite'),
    path('rooms/<uuid:pk>/leave/', views.ChatRoomLeaveView.as_view(), name='chatroom-leave'),
    
    # Messages
    path('messages/', views.MessageListView.as_view(), name='message-list'),
    path('messages/<uuid:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    path('messages/mark-as-read/', views.MessageMarkAsReadView.as_view(), name='message-mark-read'),
    
    # Encryption keys
    path('encryption-keys/', views.EncryptionKeyListView.as_view(), name='encryptionkey-list'),
    
    # User search and presence
    path('users/search/', views.UserSearchView.as_view(), name='user-search'),
    path('presence/', views.UserPresenceListView.as_view(), name='user-presence'),
    
    # File uploads
    path('files/', views.FileUploadView.as_view(), name='file-upload'),
    
    # Include router URLs for mentor-talent chat
    path('', include(router.urls)),
]