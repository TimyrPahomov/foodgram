from rest_framework import serializers

from recipes.models import User


class UserCreateSerializer(serializers.Serializer):
    """Сериализатор для аутентификации и создания новых пользователей."""

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


class UserRepresentationSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации и создания новых пользователей.

    Вызывается для представления данных при создании пользователя.
    """

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name')
