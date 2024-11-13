from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from api.filter import RecipeFilter, NameSearchFilter
from api.permissions import UpdateDeletePermission
from api.renderers import TextIngredientDataRenderer
from api.serializers import (FollowSerializer, RecipeIngredients,
                             IngredientSerializer,
                             IngredientReadSerializer, RecipeSerializer,
                             RecipeMiniSerializer, RecipeReadSerializer,
                             TagSerializer, UserAvatarSerializer,
                             UserCreateSerializer,
                             UserPasswordChangeSerializer,
                             UserFollowSerializer, UserSerializer)
from recipes.models import (Favorite, Follow, Ingredient,
                            Recipe, ShoppingCart, Tag, User)
from utils.constants import (AVATAR_PATH, FAVORITE_PATH, PASSWORD_CHANGE_PATH,
                             RECIPE_LINK_PATH, SHOPPING_CART_PATH,
                             SUBSCRIBE_PATH, SUBSCRIPTIONS_PATH, USER_PROFILE)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Набор представлений для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


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
    filterset_class = RecipeFilter
    permission_classes = (UpdateDeletePermission,)
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от метода запроса."""
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeSerializer

    @action(
        detail=False, methods=['get'], url_path='download_shopping_cart',
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
        return Response(serializer.data, headers={"Content-Disposition": f'attachment; filename="{file_name}"'})

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

    @action(
        detail=True, methods=['get'], url_path=RECIPE_LINK_PATH,
        permission_classes=(permissions.AllowAny,)
    )
    def get_link(self, request, pk):
        """Отвечает за выдачу ссылки на рецепт."""
        return HttpResponse(request.build_absolute_uri(f'/api/recipes/{pk}/'))


class UserViewSet(viewsets.ModelViewSet):
    """Представление для работы с учётными записями пользователей."""

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete']
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitOffsetPagination
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
            serializer = UserFollowSerializer(
                user,
                context={'request': request},
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
        detail=False, methods=['get'], url_path=SUBSCRIPTIONS_PATH,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        """
        Возвращает пользователей, на которых подписан текущий пользователь.
        """
        user = request.user
        followings = self.paginate_queryset(Follow.objects.filter(user=user))
        serializer = FollowSerializer(
            followings,
            context={'request': request},
            many=True
        )
        if followings:
            return self.get_paginated_response(data=serializer.data)
        return Response(
            'Вы не подписаны ни на одного пользователя.',
            status=status.HTTP_200_OK
        )

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


# class SubscribeViewSet(viewsets.ModelViewSet):
#     """Представление для работы с учётными записями пользователей."""

#     serializer_class = FollowSerializer
#     http_method_names = ['post', 'delete']
#     pagination_class = LimitOffsetPagination
#     permission_classes = (permissions.IsAuthenticated,)

#     def get_queryset(self):
#         return Follow.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         user_id = int(self.kwargs['id'])
#         user = User.objects.filter(id=user_id).first()
#         follower = self.request.user
#         Follow.objects.filter(
#                 user=follower, following=user
#             )
#         serializer.save(following=user)
