from rest_framework import serializers

from api.common_serializers import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredients, Tag, User
from utils.constants import USERNAME_REGEX


class IngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        model = Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Вызывается для представления данных при создании рецепта.
    """

    id = serializers.IntegerField(source='ingredients.id')
    name = serializers.CharField(source='ingredients.name')
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )
        model = RecipeIngredients


class IngredientCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Вызывается для передачи данных при создании рецепта.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        fields = (
            'id',
            'amount',
        )
        model = RecipeIngredients


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""

    class Meta:
        fields = (
            'id',
            'name',
            'slug',
        )
        model = Tag


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с учётными записями пользователей."""

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
        )
        model = User


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для аутентификации и создания новых пользователей."""

    email = serializers.EmailField(required=True)
    username = serializers.RegexField(
        regex=USERNAME_REGEX,
        required=True
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def to_representation(self, instance):
        """Возвращает данные в формате с вложенными сериализаторами."""
        serializer = UserSerializer(instance)
        return serializer.data

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует.'
            )
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {'Пользователь с таким email уже существует.'}
            )
        return data


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с рецептами."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def to_representation(self, instance):
        """Возвращает данные в формате с вложенными сериализаторами."""
        serializer = RecipeReadSerializer(instance)
        return serializer.data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredients=ingredients['id'],
                amount=ingredients['amount']
            )
        return recipe


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с рецептами.

    Вызывается для безопасных методов.
    """

    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(read_only=True, many=True)
    image = Base64ImageField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe
