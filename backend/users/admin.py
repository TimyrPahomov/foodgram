from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    """Админ-зона Пользователей."""

    model = FoodgramUser
    list_display = ('first_name', 'last_name', 'username', 'email', 'avatar')
    search_fields = ('first_name', 'email')
    list_filter = ('first_name',)
