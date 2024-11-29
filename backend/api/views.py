from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filter import NameSearchFilter, RecipeFilter
from api.permissions import UpdateDeletePermission
from api.serializers import (
    FavoriteSerializer,
    FollowReadSerializer,
    FollowSerializer,
    IngredientReadSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserAvatarSerializer
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
    RECIPE_LINK_PATH,
    RECIPE_NOT_IN_FAVORITE_MESSAGE,
    RECIPE_NOT_IN_SHOPPING_CART_MESSAGE,
    SHOPPING_CART_PATH,
    SUBSCRIBE_PATH,
    SUBSCRIPTIONS_PATH,
    USER_NOT_SUBSCRIBE_MESSAGE
)
from utils.functions import (
    add_object,
    remove_object,
    shopping_cart_file_create
)


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

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (UpdateDeletePermission,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    ordering_fields = ('-pub_date',)

    def get_queryset(self):
        """
        Возвращает список рецептов.

        Осуществляет предзагрузку связанных объектов из моделей User,
        Tag и Ingredient.
        """
        return Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredients'
        )

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
        if request.method == 'POST':
            return add_object(
                request,
                pk,
                ShoppingCartSerializer
            )
        return remove_object(
            ShoppingCart, request.user, pk, RECIPE_NOT_IN_SHOPPING_CART_MESSAGE
        )

    @action(
        detail=False, methods=['get'], url_path=DOWNLOAD_SHOPPING_CART_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Отвечает за выгрузку списка покупок."""
        ingredients = Ingredient.objects.filter(
            recipes__shopping_carts__user=self.request.user
        ).annotate(total_amount=Sum('recipe_ingredients__amount'))
        return shopping_cart_file_create(ingredients)

    @action(
        detail=True, methods=['post', 'delete'], url_path=FAVORITE_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Отвечает за работу с избранными рецептами."""
        if request.method == 'POST':
            return add_object(
                request,
                pk,
                FavoriteSerializer
            )
        return remove_object(
            Favorite, request.user, pk, RECIPE_NOT_IN_FAVORITE_MESSAGE
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


class FoodgramUserViewSet(UserViewSet):
    """Представление для работы с учётными записями пользователей."""

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete']
    filter_backends = (DjangoFilterBackend,)

    def get_permissions(self):
        if self.action in [
            'me', 'set_password', 'subscribe', 'subscriptions', 'avatar'
        ]:
            permission_classes = (permissions.IsAuthenticated,)
        else:
            permission_classes = (permissions.AllowAny,)

        return [permission() for permission in permission_classes]

    @action(
        detail=True, methods=['post', 'delete'], url_path=SUBSCRIBE_PATH
    )
    def subscribe(self, request, id):
        """Отвечает за работу c подписками."""
        user = request.user
        if request.method == 'POST':
            serializer = FollowSerializer(
                context={'request': request},
                data={
                    'user': user.id,
                    'following': id,
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        if Follow.objects.filter(
            user=user, following_id=id
        ).delete()[0] == 0:
            return Response(
                USER_NOT_SUBSCRIBE_MESSAGE,
                status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], url_path=SUBSCRIPTIONS_PATH
    )
    def subscriptions(self, request):
        """
        Возвращает пользователей, на которых подписан текущий пользователь.
        """
        followings = self.paginate_queryset(
            Follow.objects.filter(
                user=request.user
            ).annotate(recipes_count=Count('following__recipes')))
        serializer = FollowReadSerializer(
            followings,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(data=serializer.data)

    @action(
        detail=False, methods=['put', 'delete'], url_path=AVATAR_PATH
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
