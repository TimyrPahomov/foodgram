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
    list_filter = ('tags',)
    search_fields = ('name', 'author__first_name', 'author__last_name')
    inlines = (RecipeIngredientsInline, RecipeTagsInline)

    @admin.display(description='Количество добавлений в избранное.')
    def in_favorite_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return Favorite.objects.filter(recipe_id=obj.id).count()

    def get_queryset(self, request):
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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс для представления тегов в Админ-зоне."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug',)


@admin.register(Favorite)
class FavoriteAdmin(UserRecipeAdmin):
    """Класс для представления избранного в Админ-зоне."""

    def get_queryset(self, request):
        """
        Возвращает избранные рецепты.

        Осуществляет предзагрузку связанных объектов из моделей User и Recipe.
        """
        return ShoppingCart.objects.select_related(
            'user', 'recipe'
        )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Класс для представления подписок в Админ-зоне."""

    list_display = ('user', 'following')
    search_fields = ('user__first_name', 'following__first_name')

    def get_queryset(self, request):
        """
        Возвращает подписки пользователя.

        Осуществляет предзагрузку связанных объектов из модели User.
        """
        return Follow.objects.select_related(
            'user', 'following'
        )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeAdmin):
    """Класс для представления списка покупок в Админ-зоне."""

    def get_queryset(self, request):
        """
        Возвращает список покупок.

        Осуществляет предзагрузку связанных объектов из моделей User и Recipe.
        """
        return ShoppingCart.objects.select_related(
            'user', 'recipe'
        )
