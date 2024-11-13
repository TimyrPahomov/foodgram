from django_filters import rest_framework as filter, MultipleChoiceFilter
from django_filters.fields import MultipleChoiceField
from rest_framework import filters
from recipes.models import Recipe


class MultipleCharField(MultipleChoiceField):
    def validate(self, _):
        pass


class MultipleCharFilter(MultipleChoiceFilter):
    field_class = MultipleCharField


class RecipeFilter(filter.FilterSet):
    """Фильтр для работы с рецептом."""

    is_favorited = filter.BooleanFilter(method='favorite_value')
    is_in_shopping_cart = filter.BooleanFilter(method='shopping_cart_value')
    tags = MultipleCharFilter(field_name='tags__slug', lookup_expr="contains")

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'tags', 'author')

    def favorite_value(self, queryset, name, value):
        if not value:
            return queryset
        queryset = queryset.filter(
            **{'favorite__user_id': self.request.user.pk}
        )
        return queryset

    def shopping_cart_value(self, queryset, name, value):
        if not value:
            return queryset
        queryset = queryset.filter(
            **{'shoppingcart__user_id': self.request.user.pk}
        )
        return queryset


class NameSearchFilter(filters.SearchFilter):
    search_param = "name"
