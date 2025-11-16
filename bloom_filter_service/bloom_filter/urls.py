from django.urls import path
from . import views

urlpatterns = [
    # Check endpoints
    path('check/username/', views.CheckUsernameView.as_view(), name='check-username'),
    path('check/email/', views.CheckEmailView.as_view(), name='check-email'),
    path('check/both/', views.CheckBothView.as_view(), name='check-both'),
    
    # Add endpoints
    path('add/username/', views.AddUsernameView.as_view(), name='add-username'),
    path('add/email/', views.AddEmailView.as_view(), name='add-email'),
    path('add/user/', views.AddUserView.as_view(), name='add-user'),
    
    # Management endpoints
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('rebuild/', views.RebuildView.as_view(), name='rebuild'),
    path('clear/', views.ClearView.as_view(), name='clear'),
    
    # Utility endpoints
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('webhook/', views.WebhookView.as_view(), name='webhook'),
]