
from django.urls import path
from . import views

urlpatterns = [
    path("user-profiles/", views.AllUserProfiles, name='user-profiles'),
    path("profiles/me/", views.MyProfileView.as_view(), name="profile-me"),
    path("profiles/me/avatar/", views.AvatarUploadView.as_view(), name="profile-avatar"),
    path('profiles/me/resume/', views.ResumeUploadView.as_view(), name='profile-resume'),
    path('profile/<uuid:id>/', views.PublicProfileView, name="public-profile"),
    path('job-roles/', views.JobRoleList.as_view(), name='job-roles'),
    path('job-roles/<uuid:pk>/', views.JobRoleDetail.as_view(), name='job-role-detail'),

    # Test endpoint for permission verification
    # path("test-permission/", views.test_permission_endpoint, name='test-permission'),
]
