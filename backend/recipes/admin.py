from django.contrib import admin
from django.db import models

from recipes.models import (
    Ingredient, Recipe,
    RecipeIngredients, ShortLink, Tag
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-зона Ингредиента."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('recipe__name', 'name')
    list_filter = ('name', 'measurement_unit')


class RecipeIngredientsInline(admin.TabularInline):
    """Выбор Ингредиентов для Рецептов."""

    model = RecipeIngredients


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-зона Рецептов."""

    list_display = (
        'id', 'name', 'author', 'image', 'text', 'cooking_time'
    )
    # list_display_links = ('name',)
    list_filter = ('author', 'cooking_time', 'tags')
    search_fields = ('name',)
    inlines = (RecipeIngredientsInline,)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-зона Тегов."""

    list_display = ('name', 'slug')
    # list_display_links = ('text',)
    list_filter = ('name',)
    search_fields = ('slug',)


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    """Админ-зона ссылок."""

    list_display = ('full_link', 'short_link')
    search_fields = ('full_link',)
