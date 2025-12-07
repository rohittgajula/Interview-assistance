"""
Custom permission classes for interview_service API endpoints.
Implements role-based access control for candidates, interviewers, and org admins.
"""

from rest_framework import permissions


class IsCandidate(permissions.BasePermission):
    """
    Permission class that allows only candidates.
    """
    message = "Only candidates can perform this action."

    def has_permission(self, request, view):
        return request.user and request.user.is_candidate


class IsInterviewer(permissions.BasePermission):
    """
    Permission class that allows only interviewers.
    """
    message = "Only interviewers can perform this action."

    def has_permission(self, request, view):
        return request.user and request.user.is_interviewer


class IsOrgAdmin(permissions.BasePermission):
    """
    Permission class that allows only organization admins.
    """
    message = "Only organization admins can perform this action."

    def has_permission(self, request, view):
        return request.user and request.user.is_org_admin


class IsCandidateOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows candidates to create/modify,
    but allows read-only access to all authenticated users.
    """

    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_active

        # Write permissions only for candidates
        return request.user and request.user.is_candidate


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows owners to edit their own objects,
    but provides read-only access to others.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsOwner(permissions.BasePermission):
    """
    Permission class that allows only the owner to access the object.
    """
    message = "You can only access your own resources."

    def has_object_permission(self, request, view, obj):
        # Check if object has 'user' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsOwnerOrInterviewer(permissions.BasePermission):
    """
    Permission class that allows owners or interviewers to access the object.
    Used for practice sessions and live interviews.
    """
    message = "You can only access your own sessions or sessions you're conducting."

    def has_object_permission(self, request, view, obj):
        # For practice sessions: only the user who created it
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # For live interview sessions: both interviewer and candidate
        if hasattr(obj, 'interviewer') and hasattr(obj, 'candidate'):
            return obj.interviewer == request.user or obj.candidate == request.user

        return False


class IsInterviewerForLiveSession(permissions.BasePermission):
    """
    Permission class that allows only the interviewer of a live session.
    """
    message = "Only the interviewer can perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if object has 'interviewer' attribute
        if hasattr(obj, 'interviewer'):
            return obj.interviewer == request.user

        # For related objects (questions, reports), check the live_session
        if hasattr(obj, 'live_session'):
            return obj.live_session.interviewer == request.user

        return False


class CanScheduleLiveInterview(permissions.BasePermission):
    """
    Permission class for scheduling live interviews.
    Only interviewers and org admins can schedule.
    """
    message = "Only interviewers and organization admins can schedule live interviews."

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user and (request.user.is_interviewer or request.user.is_org_admin)
        return True


class CanManageJobRoles(permissions.BasePermission):
    """
    Permission class for managing job roles.
    Only org admins can create/update/delete job roles.
    Everyone can read job roles.
    """
    message = "Only organization admins can manage job roles."

    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_active

        # Write permissions only for org admins
        return request.user and request.user.is_org_admin


class CanManageAIProviders(permissions.BasePermission):
    """
    Permission class for managing AI and speech providers.
    Only org admins can manage providers.
    """
    message = "Only organization admins can manage AI and speech providers."

    def has_permission(self, request, view):
        return request.user and request.user.is_org_admin


class CanViewAnalytics(permissions.BasePermission):
    """
    Permission class for viewing analytics.
    Users can view their own analytics.
    Org admins can view all analytics.
    """
    message = "You don't have permission to view these analytics."

    def has_permission(self, request, view):
        # Org admins can view all analytics
        if request.user.is_org_admin:
            return True

        # Other users can view their own analytics (checked in view)
        return request.user and request.user.is_active

    def has_object_permission(self, request, view, obj):
        # Org admins can view any user's analytics
        if request.user.is_org_admin:
            return True

        # Users can view their own analytics
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsAuthenticatedOrCreateOnly(permissions.BasePermission):
    """
    Permission class for endpoints that allow unauthenticated user creation
    but require authentication for other operations.
    """

    def has_permission(self, request, view):
        # Allow POST requests (creation) without authentication
        if request.method == 'POST':
            return True

        # Require authentication for all other methods
        return request.user and request.user.is_active
