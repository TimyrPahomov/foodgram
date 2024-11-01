from rest_framework import permissions


class AdminOrReadOnlyPermission(permissions.IsAuthenticatedOrReadOnly):
    """
    Класс для проверки прав пользователя.

    Предоставляет доступ на чтение всем пользователям.
    Другие действия доступны только администратору.
    """

    def has_permission(self, request, view):
        """Проверяет права пользователя."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_admin
        )


class UpdateDeletePermission(permissions.IsAuthenticatedOrReadOnly):
    """
    Класс для проверки прав пользователя.

    Предоставляет доступ на чтение всем пользователям.
    Другие действия доступны только автору.
    """

    def has_object_permission(self, request, view, obj):
        """Проверяет права пользователя для доступа к объекту."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and obj.author == request.user
        )


class AdminPermission(permissions.BasePermission):
    """
    Класс для проверки прав пользователя.

    Доступ предоставляется только администратору.
    """

    def has_permission(self, request, view):
        """Проверяет права пользователя."""
        return request.user.is_authenticated and request.user.is_admin
