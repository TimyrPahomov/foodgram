import random

from django.shortcuts import get_object_or_404, redirect
from rest_framework import serializers, status
from rest_framework.response import Response

from recipes.models import Follow, Recipe, RecipeIngredients
from utils.constants import (
    DEFAULT_RECIPES_LIMIT,
    SHORT_LINK_LENGTH,
    SYMBOLS_FOR_LINK
)


def check_value_existence(self, queryset, name, value):
    """Проверяет наличие объекта в избранном или списке покупок."""
    if not value:
        return queryset
    queryset = queryset.filter(
        **{name: self.request.user.pk}
    )
    return queryset


def check_recipes_limit_param(self, obj, serializer):
    """
    Проверяет наличие и корректность параметра 'recipes_limit'.

    Если 'recipes_limit' передан в запросе, ограничивает количество рецептов
    в ответе до значения параметра 'recipes_limit'.
    """
    request = self.context.get('request')
    recipes_limit = request.query_params.get(
        'recipes_limit',
        DEFAULT_RECIPES_LIMIT
    )
    recipes = Recipe.objects.filter(author=obj)
    if recipes_limit:
        try:
            recipes_limit = int(recipes_limit)
        except ValueError:
            raise serializers.ValidationError(
                'recipes_limit должен быть целым числом.'
            )
        if recipes_limit <= 0:
            raise serializers.ValidationError(
                'recipes_limit должен быть больше нуля.'
            )
        recipes = recipes[:recipes_limit]
    serializer = serializer(
        recipes,
        read_only=True,
        many=True
    )
    return serializer.data


def check_model_object(self, obj, model):
    """Проверяет наличие объекта в модели."""
    request = self.context.get('request')
    user = request.user
    if user.id is None:
        return False
    if isinstance(model(), Follow):
        return model.objects.filter(
            user=user, following=obj
        ).exists()
    return model.objects.filter(
        user=user, recipe=obj
    ).exists()


def add_object(
    model,
    request,
    model_object,
    serializer,
    error_message
):
    """Добавляет запись в модель."""
    user = request.user
    if model.objects.filter(
        user=user, recipe=model_object
    ).exists():
        return Response(
            error_message,
            status.HTTP_400_BAD_REQUEST
        )
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


def remove_object(
    model,
    user,
    model_object,
    error_message
):
    """Удаляет запись из модели."""
    if not model.objects.filter(
        user=user, recipe=model_object
    ).exists():
        return Response(
            error_message,
            status.HTTP_400_BAD_REQUEST
        )
    model.objects.get(
        user=user, recipe=model_object
    ).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def redirection(request, short_link):
    """Перенаправляет пользователя на рецепт по короткой ссылке"""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(
        request.build_absolute_uri(
            f'/recipes/{recipe.id}'
        )
    )


def short_link_create():
    """Генерирует короткую ссылку."""
    while True:
        short_link = ''.join(
            random.choices(
                SYMBOLS_FOR_LINK,
                k=SHORT_LINK_LENGTH
            )
        )
        if not Recipe.objects.filter(
            short_link=short_link
        ).exists():
            break
    return short_link


def create_or_update_recipe_tags_and_ingredients(tags, ingredients, recipe):
    """Добавляет теги и ингредиенты в рецепт"""
    recipe.tags.set(tags)
    all_ingredients = []
    for ingredient in ingredients:
        ingredient_data = ingredient.get('id')
        all_ingredients.append(ingredient_data)
        RecipeIngredients.objects.create(
            recipe=recipe,
            ingredients=ingredient_data,
            amount=ingredient.get('amount')
        )
    recipe.ingredients.set(all_ingredients)
