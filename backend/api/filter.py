from django_filters import MultipleChoiceFilter, rest_framework as filter
from django_filters.fields import MultipleChoiceField
from rest_framework import filters

from recipes.models import Recipe
from utils.functions import filter_queryset


class MultipleCharField(MultipleChoiceField):
    """
    Фильтр для работы с несколькими тегами.

    Изменяет метод validate.
    """

    def validate(self, _):
        pass


class MultipleCharFilter(MultipleChoiceFilter):
    """
    Фильтр для работы с несколькими тегами.

    Указывает значение для поля field_class.
    """

    field_class = MultipleCharField


class RecipeFilter(filter.FilterSet):
    """Фильтр для работы с рецептом."""

    is_favorited = filter.BooleanFilter(method='favorite_value')
    is_in_shopping_cart = filter.BooleanFilter(method='shopping_cart_value')
    tags = MultipleCharFilter(field_name='tags__slug', lookup_expr='contains')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'tags', 'author')

    def favorite_value(self, queryset, name, value):
        """Метод для получения избранных рецептов."""
        return filter_queryset(
            self, queryset, 'favorites__user_id', value
        )

    def shopping_cart_value(self, queryset, name, value):
        """Метод для получения рецептов из списка покупок."""
        return filter_queryset(
            self, queryset, 'shopping_carts__user_id', value
        )


class NameSearchFilter(filters.SearchFilter):
    """Фильтр для поиска ингредиента по названию."""

    search_param = 'name'
