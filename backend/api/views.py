import io

from django.db.models import Count, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filter import NameSearchFilter, RecipeFilter
from api.permissions import UpdateDeletePermission
from api.serializers import (
    FollowPostDeleteSerializer,
    FollowReadSerializer,
    IngredientReadSerializer,
    RecipeMiniSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
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
    INVALID_SUBSCRIBE_MESSAGE,
    RECIPE_ALREADY_IN_FAVORITE_MESSAGE,
    RECIPE_ALREADY_IN_SHOPPING_CART_MESSAGE,
    RECIPE_LINK_PATH,
    RECIPE_NOT_IN_FAVORITE_MESSAGE,
    RECIPE_NOT_IN_SHOPPING_CART_MESSAGE,
    SHOPPING_CART_PATH,
    SUBSCRIBE_PATH,
    SUBSCRIBE_TO_YOURSELF_MESSAGE,
    SUBSCRIPTIONS_PATH,
    USER_ALREADY_SUBSCRIBE_MESSAGE,
    USER_NOT_SUBSCRIBE_MESSAGE
)
from utils.functions import add_object, remove_object


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
        return Recipe.objects.prefetch_related(
            'tags', 'ingredients'
        ).select_related('author')

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
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            return add_object(
                ShoppingCart,
                request,
                recipe,
                RecipeMiniSerializer,
                RECIPE_ALREADY_IN_SHOPPING_CART_MESSAGE
            )
        return remove_object(
            ShoppingCart, user, recipe, RECIPE_NOT_IN_SHOPPING_CART_MESSAGE
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
        text_buffer = io.StringIO()
        for ingredient in ingredients:
            text_buffer.write(
                '{} ({}) - {}\n'.format(
                    ingredient.name,
                    ingredient.measurement_unit,
                    ingredient.total_amount
                )
            )
        return HttpResponse(text_buffer.getvalue(), content_type='text/plain')

    @action(
        detail=True, methods=['post', 'delete'], url_path=FAVORITE_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Отвечает за работу с избранными рецептами."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            return add_object(
                Favorite,
                request,
                recipe,
                RecipeMiniSerializer,
                RECIPE_ALREADY_IN_FAVORITE_MESSAGE
            )
        return remove_object(
            Favorite, user, recipe, RECIPE_NOT_IN_FAVORITE_MESSAGE
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
        following = self.queryset.filter(
            id=id
        ).annotate(recipes_count=Count('recipes')).first()
        if following is None:
            return Response(
                INVALID_SUBSCRIBE_MESSAGE,
                status.HTTP_404_NOT_FOUND
            )
        object_filter = Follow.objects.filter(
            user=user, following=following
        )
        if request.method == 'POST':
            if object_filter.exists():
                return Response(
                    USER_ALREADY_SUBSCRIBE_MESSAGE,
                    status.HTTP_400_BAD_REQUEST
                )
            if following.id == user.id:
                return Response(
                    SUBSCRIBE_TO_YOURSELF_MESSAGE,
                    status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(
                user=user, following=following
            )
            serializer = FollowPostDeleteSerializer(
                following,
                context={'request': request}
            )
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not object_filter.exists():
            return Response(
                USER_NOT_SUBSCRIBE_MESSAGE,
                status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.get(
            user=user, following=following
        ).delete()
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
