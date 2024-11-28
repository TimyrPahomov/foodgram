from django.contrib import admin

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredients,
    RecipeTags,
    ShoppingCart,
    Tag
)


class UserRecipeAdmin(admin.ModelAdmin):
    """
    Общий класс для представления в Админ-зоне.

    Добавляет поля list_display, search_fields и list_filter.
    """

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс для представления ингредиентов в Админ-зоне."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientsInline(admin.TabularInline):
    """Выбор Ингредиентов для Рецептов."""

    model = RecipeIngredients


class RecipeTagsInline(admin.TabularInline):
    """Выбор Тегов для Рецептов."""

    model = RecipeTags


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс для представления рецептов в Админ-зоне."""

    readonly_fields = ('in_favorite_count',)
    list_display = (
        'name', 'author', 'cooking_time', 'in_favorite_count'
    )
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__first_name', 'author__last_name')
    inlines = (RecipeIngredientsInline, RecipeTagsInline)

    @admin.display(description='Количество добавлений в избранное.')
    def in_favorite_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return len(Favorite.objects.filter(recipe_id=obj.id))


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс для представления тегов в Админ-зоне."""

    list_display = ('name', 'slug')
    list_filter = ('name',)
    search_fields = ('slug',)


@admin.register(Favorite)
class FavoriteAdmin(UserRecipeAdmin):
    """Класс для представления избранного в Админ-зоне."""


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Класс для представления подписок в Админ-зоне."""

    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
    list_filter = ('user', 'following')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeAdmin):
    """Класс для представления списка покупок в Админ-зоне."""
