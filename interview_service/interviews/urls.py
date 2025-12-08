
from django.urls import path
from . import views

urlpatterns = [
    path("user-profiles/", views.AllUserProfiles, name='user-profiles'),
]
