from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsFaculty(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'faculty'

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class IsClubAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'club_admin'

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.role == 'admin'
        elif hasattr(obj, 'author'):
            return obj.author == request.user or request.user.role == 'admin'
        elif hasattr(obj, 'organizer'):
            return obj.organizer == request.user or request.user.role == 'admin'
        elif hasattr(obj, 'president'):
            return obj.president == request.user or request.user.role == 'admin'
        return False

class IsClubMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'club'):
            return obj.club.is_member(request.user) or request.user.role in ['admin', 'faculty']
        return False

class CanManageClub(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'can_manage'):
            return obj.can_manage(request.user)
        return False

class ReadOnlyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'