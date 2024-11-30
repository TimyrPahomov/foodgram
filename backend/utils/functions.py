import io
import random

from django.shortcuts import get_object_or_404, redirect
from rest_framework import serializers, status
from rest_framework.response import Response

from recipes.models import Recipe, RecipeIngredients
from utils.constants import (
    DEFAULT_RECIPES_LIMIT,
    SHORT_LINK_LENGTH,
    SYMBOLS_FOR_LINK
)


def filter_queryset(self, queryset, name, value):
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
    if not recipes_limit.isnumeric():
        raise serializers.ValidationError(
            'recipes_limit должен быть целым числом.'
        )
    recipes_limit = int(recipes_limit)
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


def add_object(
    request,
    pk,
    serializer,
):
    """Добавляет запись в модель."""
    user = request.user
    serializer = serializer(
        context={'request': request},
        data={
            'user': user.id,
            'recipe': pk,
        }
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        data=serializer.data,
        status=status.HTTP_201_CREATED
    )


def remove_object(
    model,
    user,
    pk,
    error_message
):
    """Удаляет запись из модели."""
    number_of_deleted_object, *deleted_object = model.objects.filter(
        user=user, recipe_id=pk
    ).delete()
    if number_of_deleted_object == 0:
        return Response(
            error_message,
            status.HTTP_400_BAD_REQUEST
        )
    return Response(status=status.HTTP_204_NO_CONTENT)


def redirection(request, short_link):
    """Перенаправляет пользователя на рецепт по короткой ссылке."""
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


def shopping_cart_file_create(ingredients):
    """Создаёт файл со списком покупок."""
    text_buffer = io.StringIO()
    for ingredient in ingredients:
        text_buffer.write(
            '{} ({}) - {}\n'.format(
                ingredient.name,
                ingredient.measurement_unit,
                ingredient.total_amount
            )
        )
    return text_buffer


def create_or_update_recipe_tags_and_ingredients(tags, ingredients, recipe):
    """Добавляет теги и ингредиенты в рецепт."""
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
