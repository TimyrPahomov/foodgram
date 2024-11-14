from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import serializers, status
from rest_framework.response import Response

from recipes.models import Favorite, Follow, Recipe, ShoppingCart, ShortLink
from utils.constants import SUBSCRIBE_TO_YOURSELF_MESSAGE, ZERO_VALUE


def filter_value(self, queryset, name, value):
    """Проверяет наличие объекта в избранном или списке покупок."""
    if not value:
        return queryset
    queryset = queryset.filter(
        **{'favorite__user_id': self.request.user.pk}
    )
    return queryset


def recipes_limit_validate(self, obj, serializer):
    """
    Проверяет наличие и корректность параметра 'recipes_limit'.

    Если 'recipes_limit' передан в запросе, ограничивает количество рецептов 
    в ответе до значения параметра 'recipes_limit'.
    """
    request = self.context.get('request')
    recipes_limit = request.query_params.get('recipes_limit')
    recipes = Recipe.objects.filter(author=obj)
    if recipes_limit:
        try:
            recipes_limit = int(recipes_limit)
        except ValueError:
            raise serializers.ValidationError(
                'recipes_limit должен быть целым числом.'
            )
        if recipes_limit <= ZERO_VALUE:
            raise serializers.ValidationError(
                'recipes_limit должен быть больше нуля.'
            )
        serializer = serializer(
            recipes[:recipes_limit],
            read_only=True,
            many=True
        )
    else:
        serializer = serializer(
            recipes,
            read_only=True,
            many=True
        )
    return serializer.data


def value_in_model(self, obj, model):
    """Проверяет наличие объекта в модели."""
    request = self.context.get('request')
    user = request.user
    if user.id is None:
        return False
    if model == Favorite or model == ShoppingCart:
        return model.objects.filter(
            user=user, recipe=obj
        ).exists()
    return model.objects.filter(
        user=user, following=obj
    ).exists()


def add_or_remove_object(
    self,
    request,
    model,
    serializer,
    error_message1,
    error_message2
):
    """Добавляет или удаляет запись в модель."""
    model_object = self.get_object()
    user = request.user
    if model == Follow:
        object_filter = model.objects.filter(
            user=user, following=model_object
        )
    else:
        object_filter = model.objects.filter(
            user=user, recipe=model_object
        )
    if request.method == 'POST':
        if object_filter.exists():
            return Response(
                error_message1,
                status.HTTP_400_BAD_REQUEST
            )
        if model == Follow and model_object.id == user.id:
            return Response(
                SUBSCRIBE_TO_YOURSELF_MESSAGE,
                status.HTTP_400_BAD_REQUEST
            )
        if model == Follow:
            model.objects.create(
                user=user, following=model_object
            )
        else:
            model.objects.create(
                user=user, recipe=model_object
            )
        serializer = serializer(
            model_object,
            context={'request': request}
        )
        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )
    if not object_filter.exists():
        return Response(
            error_message2,
            status.HTTP_400_BAD_REQUEST
        )
    if model == Follow:
        model.objects.get(
            user=user, following=model_object
        ).delete()
    else:
        model.objects.get(
            user=user, recipe=model_object
        ).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def redirection(request, short_url):
    """Перенаправляем пользователя на рецепт по короткой ссылке"""
    obj = get_object_or_404(ShortLink, short_link=short_url)
    full_link = obj.full_link
    return redirect(full_link)
