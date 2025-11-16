
from django.urls import path
from . import views


urlpatterns = [
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("token/refresh/", views.CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", views.logout_user, name="logout"),
    path("me/", views.get_current_user, name="me"),

    path("organizations/", views.list_organizations, name="organization_list"),
    path("organizations/<uuid:org_id>/", views.get_organization, name="organization_detail"),
    path("organizations/create/", views.create_organization, name="organization_create"),
    path("organizations/<uuid:org_id>/update/", views.update_organization, name="organization_update"),
    path("organizations/<uuid:org_id>/delete/", views.delete_organization, name="organization_delete"),

    path("organizations/<uuid:org_id>/members/", views.list_members, name="list_members"),
    path("organizations/<uuid:org_id>/members/add/", views.add_member, name="add_member"),
    path("organizations/<uuid:org_id>/members/<uuid:user_id>/remove/", views.remove_member, name="remove_member"),

    path('users/', views.UsersListView.as_view(), name='users-list'),
]


