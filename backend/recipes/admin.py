from django.contrib import admin

from recipes.common_admin import UserRecipeAdmin
from recipes.models import (
    Ingredient, Favorite, Follow, Recipe,
    RecipeIngredients, RecipeTags, ShoppingCart, Tag
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


class RecipeTagsInline(admin.TabularInline):
    """Выбор Тегов для Рецептов."""

    model = RecipeTags


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-зона Рецептов."""

    readonly_fields = ('in_favorite_count',)
    list_display = (
        'name', 'author', 'image', 'text', 'cooking_time', 'in_favorite_count'
    )
    list_filter = ('author', 'ingredients', 'tags')
    search_fields = ('name', 'author')
    inlines = (RecipeIngredientsInline, RecipeTagsInline)

    @admin.display(description='Количество добавлений в избранное.')
    def in_favorite_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return len(Favorite.objects.filter(recipe_id=obj.id))


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-зона Тегов."""

    list_display = ('name', 'slug')
    list_filter = ('name',)
    search_fields = ('slug',)


@admin.register(Favorite)
class FavoriteAdmin(UserRecipeAdmin):
    """Админ-зона Избранного."""

    pass


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Админ-зона Подписок."""

    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
    list_filter = ('user', 'following')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeAdmin):
    """Админ-зона Списка покупок."""

    pass
