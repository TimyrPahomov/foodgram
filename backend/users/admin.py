from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    """Админ-зона Пользователей."""

    model = FoodgramUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'avatar')
    search_fields = ('username', 'email')
    list_filter = ('username',)
