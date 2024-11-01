from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from api.permissions import UpdateDeletePermission
from api.serializers import (IngredientReadSerializer, RecipeSerializer,
                             RecipeReadSerializer, TagSerializer,
                             UserCreateSerializer, UserSerializer)
from api.viewset import ListViewSet
from recipes.models import Ingredient, Recipe, Tag, User


class IngredientViewSet(ListViewSet):
    """Набор представлений для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(ListViewSet):
    """Набор представлений для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Набор представлений для работы с рецептами."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (UpdateDeletePermission,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    filterset_fields = ('author', 'tags__name')

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от метода запроса."""
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Представление для работы с учётными записями пользователей."""

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от метода запроса."""
        if self.request.method in permissions.SAFE_METHODS:
            return UserSerializer
        return UserCreateSerializer
