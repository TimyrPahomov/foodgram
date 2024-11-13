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
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
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

    def validate(self, data):
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
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = RecipeIngredients.objects.filter(
                recipe=recipe,
                ingredients=ingredient.get('id'),
            )
            if current_ingredient:
                raise serializers.ValidationError(
                    'Ингредиент используется в рецепте больше одного раза.'
                )
            amount = ingredient.get('amount')
            if amount == 0:
                raise serializers.ValidationError(
                    'Количество не должно быть меньше нуля.'
                )
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredients=ingredient.get('id'),
                amount=amount
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
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('recipe_ingredients')
        all_ingredients = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            ingredient_amount = ingredient.get('amount')
            if ingredient_amount == 0:
                raise serializers.ValidationError(
                    'Количество не должно быть меньше нуля.'
                )
            RecipeIngredients.objects.get_or_create(
                recipe=instance,
                ingredients=ingredient_id,
                amount=ingredient_amount
            )
            all_ingredients.append(ingredient_id)
            if len(set(all_ingredients)) != len(all_ingredients):
                raise serializers.ValidationError(
                    'Ингредиент используется в рецепте больше одного раза.'
                )
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


class FollowSerializer(serializers.ModelSerializer):

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
    recipes_count = serializers.SerializerMethodField()
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
        request = self.context.get('request')
        user_id = request.user.id
        if request.method == 'GET':
            following_id = obj.following_id
        else:
            following_id = int(request.parser_context.get('kwargs').get('pk'))
        return Follow.objects.filter(
            user=user_id, following=following_id
        ).exists()

    def get_recipes_count(self, obj):
        request = self.context.get('request')
        if request.method == 'GET':
            following_id = obj.following_id
        else:
            following_id = int(request.parser_context.get('kwargs').get('pk'))
        return len(Recipe.objects.filter(author=following_id))

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if request.method == 'GET':
            following_id = obj.following_id
        else:
            following_id = int(request.parser_context.get('kwargs').get('pk'))
        recipes = Recipe.objects.filter(author=following_id)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise serializers.ValidationError(
                    'recipes_limit должен быть целым числом.'
                )
            if recipes_limit <= 0:
                raise serializers.ValidationError(
                    'recipes_limit должен быть больше нуля.'
                )
            serializer = RecipeMiniSerializer(
                recipes[:recipes_limit],
                read_only=True,
                many=True
            )
        else:
            serializer = RecipeMiniSerializer(
                recipes,
                read_only=True,
                many=True
            )
        return serializer.data


class UserFollowSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

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
        model = User

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return Follow.objects.filter(
            user=request.user, following=obj
        ).exists()

    def get_recipes_count(self, obj):
        return len(Recipe.objects.filter(author=obj))

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise serializers.ValidationError(
                    'recipes_limit должен быть целым числом.'
                )
            if recipes_limit <= 0:
                raise serializers.ValidationError(
                    'recipes_limit должен быть больше нуля.'
                )
            serializer = RecipeMiniSerializer(
                recipes[:recipes_limit],
                read_only=True,
                many=True
            )
        else:
            serializer = RecipeMiniSerializer(
                recipes,
                read_only=True,
                many=True
            )
        return serializer.data


# class ShortLinkSerializer(serializers.ModelSerializer):
#     """Сериализатор для изменения пароля пользователя."""

#     short_link = serializers.SerializerMethodField()

#     class Meta:
#         fields = (
#             'short_link',
#         )
#         model = Recipe

#     def get_short_link(self, obj):
#         return len(Recipe.objects.filter(author=obj))
