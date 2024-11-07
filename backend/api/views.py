from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import UpdateDeletePermission
from api.serializers import (IngredientReadSerializer, RecipeSerializer,
                             RecipeMiniSerializer, RecipeReadSerializer,
                             TagSerializer, UserAvatarSerializer,
                             UserCreateSerializer,
                             UserPasswordChangeSerializer,
                             UserWithRecipeSerializer, UserSerializer)
from recipes.models import (Favorite, Follow, Ingredient,
                            Recipe, ShoppingCart, Tag, User)
from utils.constants import (AVATAR_PATH, FAVORITE_PATH, PASSWORD_CHANGE_PATH,
                             SHOPPING_CART_PATH, SUBSCRIBE_PATH, USER_PROFILE)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Набор представлений для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Набор представлений для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


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

    @action(
        detail=True, methods=['post', 'delete'], url_path=FAVORITE_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Отвечает за работу с избранными рецептами."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    "Рецепт уже добавлен в избранное",
                    status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeMiniSerializer(
                recipe,
                context={'request': request}
            )
            Favorite.objects.create(
                user=user, recipe=recipe
            )
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                "Рецепт отсутствует в избранном",
                status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.get(
            user=user, recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', 'delete'], url_path=SHOPPING_CART_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Отвечает за работу со списком покупок."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    "Рецепт уже в списке покупок.",
                    status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeMiniSerializer(
                recipe,
                context={'request': request}
            )
            ShoppingCart.objects.create(
                user=user, recipe=recipe
            )
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                "Рецепт отсутствует в списке покупок.",
                status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.get(
            user=user, recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    @action(
        detail=True, methods=['post', 'delete'], url_path=SUBSCRIBE_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, pk):
        """Отвечает за работу c подписками."""
        user = self.get_object()
        follower = request.user
        if request.method == 'POST':
            if Follow.objects.filter(
                user=follower, following=user
            ).exists():
                return Response(
                    "Вы уже подписаны на этого пользователя.",
                    status.HTTP_400_BAD_REQUEST
                )
            if user.id == follower.id:
                return Response(
                    "Нельзя подписаться на себя.",
                    status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(
                user=follower, following=user
            )
            serializer = UserWithRecipeSerializer(
                user,
                context={'request': request}
            )
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not Follow.objects.filter(
            user=follower, following=user
        ).exists():
            return Response(
                "Вы ещё не подписаны на данного пользователя.",
                status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.get(
            user=follower, following=user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], url_path=USER_PROFILE,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        """Отвечает за работу с собственной учетной записью."""
        user = request.user
        serializer = self.get_serializer(
            user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=['put', 'delete'], url_path=AVATAR_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def avatar(self, request):
        """Отвечает за работу с аватаром пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user,
                context={'request': request},
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['post'], url_path=PASSWORD_CHANGE_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def set_password(self, request):
        """Отвечает за изменение пароля текущего пользователя."""
        user = request.user
        serializer = UserPasswordChangeSerializer(
            user,
            context={'request': request},
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        passwords = serializer.context.get('request')
        if not user.check_password(
            passwords.data.get("current_password")
        ):
            return Response(
                {'current_password': "Неверно введено значение пароля."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(
            passwords.data.get("new_password")
        )
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
