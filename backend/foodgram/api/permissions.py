from rest_framework import permissions


class AuthenticatedOrReadOnlyPermission(permissions.BasePermission):
    """
    Полное разрешение для аутентифицированных пользователей,
    только чтение для остальных.
    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or 
            request.user.is_authenticated
    )


class IsOwnerOrReadOnlyPermission(permissions.BasePermission):
    """
    Разрешение на доступ к объектам для аутентифицированных
    пользователей.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated
