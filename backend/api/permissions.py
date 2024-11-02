from rest_framework import permissions


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
