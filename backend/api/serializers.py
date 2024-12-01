import base64

from django.core.files.base import ContentFile
from django.db.models import Count
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Tag,
    User
)
from utils.constants import (
    DEFAULT_AMOUNT_VALUE,
    RECIPE_ALREADY_IN_FAVORITE_MESSAGE,
    RECIPE_ALREADY_IN_SHOPPING_CART_MESSAGE,
    SUBSCRIBE_TO_YOURSELF_MESSAGE,
    USER_ALREADY_SUBSCRIBE_MESSAGE
)
from utils.functions import (
    check_recipes_limit_param,
    create_or_update_recipe_tags_and_ingredients,
    short_link_create
)


class Base64ImageField(serializers.ImageField):
    """Поле для кодирования изображений."""

    def to_internal_value(self, data):
        """Проверяет запрос на обновление изображения в сериализаторе."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserRecipeCartSerializer(serializers.ModelSerializer):
    """Общий сериализатор для работы со списком покупок и избранным."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        fields = (
            'user',
            'recipe'
        )

    def to_representation(self, instance):
        """Возвращает данные в формате с вложенным сериализатором."""
        serializer = RecipeMiniSerializer(
            Recipe.objects.filter(id=instance.recipe_id).first(),
            context={'request': self.context.get('request')}
        )
        return serializer.data


class FavoriteSerializer(UserRecipeCartSerializer):
    """Сериализатор для работы с избранными рецептами."""

    class Meta:
        fields = (
            'user',
            'recipe'
        )
        model = Favorite

    def validate(self, data):
        """Проверяет ингредиенты и теги на корректность заполнения."""
        recipe = data.get('recipe')
        user = data.get('user')
        if Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                RECIPE_ALREADY_IN_FAVORITE_MESSAGE
            )
        return data


class ShoppingCartSerializer(UserRecipeCartSerializer):
    """Сериализатор для работы со списком покупок."""

    class Meta:
        fields = (
            'user',
            'recipe'
        )
        model = ShoppingCart

    def validate(self, data):
        """Проверяет ингредиенты и теги на корректность заполнения."""
        recipe = data.get('recipe')
        user = data.get('user')
        if ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                RECIPE_ALREADY_IN_SHOPPING_CART_MESSAGE
            )
        return data


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


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Вызывается для представления данных в рецепте.
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


class IngredientReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с ингредиентами.

    Вызывается для получения данных об ингредиентах.
    """

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""

    class Meta:
        fields = (
            'id',
            'name',
            'slug',
        )
        model = Tag


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с аватарами пользователя."""

    avatar = Base64ImageField()

    class Meta:
        fields = (
            'avatar',
        )
        model = User


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новых пользователей."""

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
        extra_kwargs = {
            'username': {
                'error_messages': {
                    'max_length': (
                        'Имя пользователя не должно быть длиннее 150 символов.'
                    ),
                },
            },
            'email': {
                'error_messages': {
                    'max_length': 'Почта не должна быть длиннее 254 символов.',
                },
            },
            'first_name': {
                'error_messages': {
                    'max_length': 'Имя не должно быть длиннее 150 символов.',
                },
            },
            'last_name': {
                'error_messages': {
                    'max_length': (
                        'Фамилия не должна быть длиннее 150 символов.'
                    ),
                },
            },
        }

    def create(self, validated_data):
        """Создаёт нового пользователя."""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


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
        """Проверяет текущую подписку на другого пользователя."""
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated and Follow.objects.filter(
            user=user, following=obj
        ).exists():
            return True
        return False


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

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
        )
        model = Recipe

    def to_representation(self, instance):
        """Возвращает данные в формате с вложенными сериализаторами."""
        serializer = RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def validate(self, data):
        """Проверяет ингредиенты и теги на корректность заполнения."""
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Должен быть хотя бы один тег.'
            )
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                'Тег используется в рецепте больше одного раза.'
            )
        ingredients = data.get('recipe_ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть хотя бы один ингредиент.'
            )
        all_ingredients = []
        for ingredient in ingredients:
            all_ingredients.append(ingredient.get('id'))
            if ingredient.get('amount', DEFAULT_AMOUNT_VALUE) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиентов не должно быть меньше нуля.'
                )
        if len(set(all_ingredients)) != len(all_ingredients):
            raise serializers.ValidationError(
                'Ингредиент используется в рецепте больше одного раза.'
            )
        return data

    def create(self, validated_data):
        """Создаёт новый рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        validated_data['short_link'] = short_link_create()
        validated_data['author'] = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data)
        create_or_update_recipe_tags_and_ingredients(tags, ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        create_or_update_recipe_tags_and_ingredients(
            tags, ingredients, instance
        )
        return super().update(instance, validated_data)


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
        """Проверяет нахождение рецепта в избранном."""
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated and Favorite.objects.filter(
            user=user, recipe=obj
        ).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет нахождение рецепта в списке покупок."""
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated and ShoppingCart.objects.filter(
            user=user, recipe=obj
        ).exists():
            return True
        return False


class FollowReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с подписками.

    Вызывается для получения подписок пользователя.
    """

    email = serializers.EmailField(source='following.email', read_only=True)
    id = serializers.IntegerField(source='following.id', read_only=True)
    username = serializers.CharField(
        source='following.username', read_only=True)
    first_name = serializers.CharField(
        source='following.first_name', read_only=True)
    last_name = serializers.CharField(
        source='following.last_name', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    avatar = Base64ImageField(source='following.avatar', read_only=True)

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        model = Follow

    def get_is_subscribed(self, obj):
        """Проверяет текущую подписку на другого пользователя."""
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated and Follow.objects.filter(
            user=user, following=obj.following
        ).exists():
            return True
        return False

    def get_recipes(self, obj):
        """
        Возвращает список рецептов пользователей в подписках.

        С помощью параметра 'recipes_limit' можно регулировать
        количество выводимых рецептов.
        """
        return check_recipes_limit_param(
            self,
            obj.following,
            RecipeMiniSerializer
        )


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с подписками пользователя."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        fields = (
            'user',
            'following'
        )
        model = Follow

    def to_representation(self, instance):
        """Возвращает данные в формате с вложенным сериализатором."""
        serializer = FollowReadSerializer(
            Follow.objects.filter(following_id=instance.following_id).annotate(
                recipes_count=Count('following__recipes')
            ).first(),
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def validate(self, data):
        """Проверяет подписки на корректность заполнения."""
        following = data.get('following')
        user = data.get('user')
        if Follow.objects.filter(
            user=user, following=following
        ).exists():
            raise serializers.ValidationError(USER_ALREADY_SUBSCRIBE_MESSAGE)
        if following.id == user.id:
            raise serializers.ValidationError(SUBSCRIBE_TO_YOURSELF_MESSAGE)
        return data
