
from django.urls import path
from . import views

urlpatterns = [
    path("user-profiles/", views.AllUserProfiles, name='user-profiles'),
    path("profiles/me/", views.MyProfileView.as_view(), name="profile-me"),
    path("profiles/me/avatar/", views.AvatarUploadView.as_view(), name="profile-avatar"),
    path('profiles/me/resume/', views.ResumeUploadView.as_view(), name='profile-resume'),

    # Test endpoint for permission verification
    # path("test-permission/", views.test_permission_endpoint, name='test-permission'),
]
