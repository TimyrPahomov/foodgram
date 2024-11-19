from django.contrib import admin


class UserRecipeAdmin(admin.ModelAdmin):
    """
    Модель для Админ-зоны.

    Добавляет поля list_display, search_fields и list_filter.
    """

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
