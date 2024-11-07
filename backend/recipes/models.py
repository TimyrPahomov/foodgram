from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from utils.constants import (
    INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH, INGREDIENT_NAME_MAX_LENGTH,
    INVALID_COOKING_TIME_MESSAGE, MAX_REPR_LENGTH, MIN_COOKING_TIME,
    RECIPE_NAME_MAX_LENGTH, TAG_MAX_LENGTH
)

User = get_user_model()


class Tag(models.Model):
    """Модель Тега."""

    name = models.CharField(
        'Название',
        max_length=TAG_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField('Слаг', max_length=TAG_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:MAX_REPR_LENGTH]


class Ingredient(models.Model):
    """Модель Ингредиента."""

    name = models.CharField(
        'Название',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name[:MAX_REPR_LENGTH]


class RecipeTags(models.Model):
    """Промежуточная модель для связи Рецепта и Тега."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    tags = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'tags'),
                name='unique_tag_for_recipe',
            ),
        )
        verbose_name = 'тег рецепта'
        verbose_name_plural = 'Теги рецепта'

    def __str__(self):
        return f'{self.recipe} - {self.tags}'


class RecipeIngredients(models.Model):
    """Промежуточная модель для связи Рецепта и Ингредиента."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField('Количество', default=0)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredients'),
                name='unique_ingredient_for_recipe',
            ),
        )
        default_related_name = 'recipe_ingredients'
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return f'{self.recipe} - {self.ingredients}'


class Recipe(models.Model):
    """Модель Рецепта."""

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(
        'Название',
        max_length=RECIPE_NAME_MAX_LENGTH,
    )
    image = models.ImageField(
        'Картинка готового блюда',
        upload_to='recipes/image/',
        null=True,
        default=None
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(MIN_COOKING_TIME,
                              message=INVALID_COOKING_TIME_MESSAGE),
        )
    )
    tags = models.ManyToManyField(
        Tag,
        through=RecipeTags,
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through=RecipeIngredients,
        verbose_name='Ингредиенты',
    )

    class Meta:
        default_related_name = 'recipes'
        ordering = ('name',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:MAX_REPR_LENGTH]


class UserRecipeModel(models.Model):
    """Абстрактная модель. Добавляет поля user и recipe."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeModel):
    """Модель Избранного."""

    class Meta(UserRecipeModel.Meta):
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(UserRecipeModel):
    """Модель Списка покупок."""

    class Meta(UserRecipeModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'


class Follow(models.Model):
    """Модель Подписки."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE)

    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follows')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user__exact=models.F('following')),
                name='follow_user_not_exact_following'
            ),
        ]
