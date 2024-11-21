from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filter import NameSearchFilter, RecipeFilter
from api.permissions import UpdateDeletePermission
from api.renderers import TextIngredientDataRenderer
from api.serializers import (
    FollowPostDeleteSerializer,
    FollowReadSerializer,
    IngredientReadSerializer,
    IngredientSerializer,
    RecipeIngredients,
    RecipeMiniSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserCreateSerializer,
    UserPasswordChangeSerializer,
    UserSerializer
)
from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
    User
)
from utils.constants import (
    AVATAR_PATH,
    DOWNLOAD_SHOPPING_CART_PATH,
    FAVORITE_PATH,
    PASSWORD_CHANGE_PATH,
    RECIPE_ALREADY_IN_FAVORITE_MESSAGE,
    RECIPE_ALREADY_IN_SHOPPING_CART_MESSAGE,
    RECIPE_LINK_PATH,
    RECIPE_NOT_IN_FAVORITE_MESSAGE,
    RECIPE_NOT_IN_SHOPPING_CART_MESSAGE,
    SHOPPING_CART_PATH,
    SUBSCRIBE_PATH,
    SUBSCRIPTIONS_PATH,
    USER_ALREADY_SUBSCRIBE_MESSAGE,
    USER_NOT_SUBSCRIBE_MESSAGE,
    USER_PROFILE
)
from utils.functions import add_or_remove_object


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Набор представлений для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Набор представлений для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Набор представлений для работы с рецептами."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (UpdateDeletePermission,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    ordering_fields = ('-pub_date',)

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от метода запроса."""
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeSerializer

    @action(
        detail=True, methods=['post', 'delete'], url_path=SHOPPING_CART_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Отвечает за работу со списком покупок."""
        return add_or_remove_object(
            self,
            request,
            ShoppingCart,
            RecipeMiniSerializer,
            RECIPE_ALREADY_IN_SHOPPING_CART_MESSAGE,
            RECIPE_NOT_IN_SHOPPING_CART_MESSAGE
        )

    @action(
        detail=False, methods=['get'], url_path=DOWNLOAD_SHOPPING_CART_PATH,
        renderer_classes=[TextIngredientDataRenderer],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Отвечает за выгрузку списка покупок."""
        queryset = RecipeIngredients.objects.filter(
            recipe__shoppingcart__user=self.request.user
        )
        file_name = "Список ингредиентов"
        serializer = IngredientSerializer(
            queryset,
            context={'request': request},
            many=True
        )
        return Response(
            serializer.data,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )

    @action(
        detail=True, methods=['post', 'delete'], url_path=FAVORITE_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Отвечает за работу с избранными рецептами."""
        return add_or_remove_object(
            self,
            request,
            Favorite,
            RecipeMiniSerializer,
            RECIPE_ALREADY_IN_FAVORITE_MESSAGE,
            RECIPE_NOT_IN_FAVORITE_MESSAGE
        )

    @action(
        detail=True, methods=['get'], url_path=RECIPE_LINK_PATH,
        permission_classes=(permissions.AllowAny,)
    )
    def get_link(self, request, pk):
        """Отвечает за выдачу короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_link = request.build_absolute_uri(
            f'/s/{recipe.short_link}'
        )
        return Response(
            {'short-link': short_link}
        )


class UserViewSet(viewsets.ModelViewSet):
    """Представление для работы с учётными записями пользователей."""

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete']
    filter_backends = (DjangoFilterBackend,)

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
        return add_or_remove_object(
            self,
            request,
            Follow,
            FollowPostDeleteSerializer,
            USER_ALREADY_SUBSCRIBE_MESSAGE,
            USER_NOT_SUBSCRIBE_MESSAGE
        )

    @action(
        detail=False, methods=['get'], url_path=SUBSCRIPTIONS_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        """
        Возвращает пользователей, на которых подписан текущий пользователь.
        """
        followings = self.paginate_queryset(
            Follow.objects.filter(user=request.user))
        serializer = FollowReadSerializer(
            followings,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(data=serializer.data)

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
