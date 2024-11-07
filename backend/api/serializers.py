from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from api.common_serializers import Base64ImageField
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredients, ShoppingCart, Tag, User)
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

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        model = User

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.id is None:
            return False
        return Follow.objects.filter(
            user=user, following=obj
        ).exists()


class UserWithRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с учётными записями пользователей.

    Вызывается для передачи данных пользователей,
    на которых подписан текущий пользователь.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        model = User

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.id is None:
            return False
        return Follow.objects.filter(
            user=user, following=obj
        ).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для аутентификации и создания новых пользователей."""

    email = serializers.EmailField(required=True)
    username = serializers.RegexField(
        regex=USERNAME_REGEX,
        required=True
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

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

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = IngredientCreateSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()

    class Meta:
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )
        model = Recipe

    def to_representation(self, instance):
        """Возвращает данные в формате с вложенными сериализаторами."""
        serializer = RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = RecipeIngredients.objects.filter(
                recipe=recipe,
                ingredients=ingredient['id'],
            )
            if current_ingredient:
                raise serializers.ValidationError(
                    'Ингредиент используется в рецепте больше одного раза.'
                )
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredients=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)
        if 'recipe_ingredients' in validated_data:
            ingredients = validated_data.pop('recipe_ingredients')
            all_ingredients = []
            for ingredient in ingredients:
                ingredient_id = ingredient['id']
                ingredient_amount = ingredient['amount']
                current_ingredient = RecipeIngredients.objects.filter(
                    recipe=instance,
                    ingredients=ingredient_id,
                )
                if current_ingredient:
                    current_ingredient.update(
                        recipe=instance,
                        ingredients=ingredient_id,
                        amount=ingredient_amount
                    )
                else:
                    RecipeIngredients.objects.get_or_create(
                        recipe=instance,
                        ingredients=ingredient_id,
                        amount=ingredient_amount
                    )
                all_ingredients.append(ingredient_id)
            instance.ingredients.set(all_ingredients)
        instance.save()
        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с рецептами.

    Передаёт полную информацию о рецепте.
    """

    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(
        read_only=True,
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.id is None:
            return False
        return Favorite.objects.filter(
            user=user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.id is None:
            return False
        return ShoppingCart.objects.filter(
            user=user, recipe=obj
        ).exists()


class RecipeMiniSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с рецептами.

    Передаёт сокращенную информацию о рецепте.
    """

    image = Base64ImageField()

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        model = Recipe


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с аватарами пользователя."""

    avatar = Base64ImageField()

    class Meta:
        fields = (
            'avatar',
        )
        model = User


class UserPasswordChangeSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения пароля пользователя."""

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        fields = (
            'new_password',
            'current_password',
        )
        model = User
