from rest_framework import mixins, permissions, viewsets


class ListViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Базовое представление для Ингредиентов и Тегов."""

    permission_classes = (permissions.AllowAny,)
