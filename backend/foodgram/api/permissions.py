from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Полное разрешение для аутентифицированных пользователей,
    только чтение для остальных.
    """
    def has_permission(self, request, view):
        if (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        ):
            return True
        return False


class IsAuthenticatedForDetail(permissions.BasePermission):
    """
    Разрешение на доступ к объектам для аутентифицированных
    пользователей.
    """
    def has_object_permission(self, request, view, obj):
        if (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        ):
            return True
        return False
