from django.db import models
from django_filters import CharFilter, FilterSet
from recipes.models import Favorite, Recipe, ShoppingCart, User


class RecipeFilter(FilterSet):
    """Фильт рецептов по url параметрам."""
    is_favorited = CharFilter(method='get_favorited')
    is_in_shopping_cart = CharFilter(method='get_shop_cart')
    author = CharFilter(method='get_author')

    class Meta:
        model = Recipe
        fields = [
            'is_favorited',
            'is_in_shopping_cart',
            'author',
        ]

    def get_favorited(self, queryset, name, value):
        username = self.request.user
        if username.is_authenticated:
            user = User.objects.get(username=username)
        else:
            user = None
        if user and value == '1':
            return queryset.filter(
                id__in=Favorite.objects
                .filter(user=user).values('recipe__id'))
        return queryset.none()

    def get_author(self, queryset, name, value):
        return queryset.filter(
            author=User.objects.get(id=value),
        )

    def get_shop_cart(self, queryset, name, value):
        username = self.request.user
        if username.is_authenticated:
            user = User.objects.get(username=username)
        else:
            user = None
        if user and value == '1':
            return (
                queryset
                .filter(id__in=ShoppingCart.objects
                        .filter(user=user).values('recipe__id'))
            )
        return queryset.none()

    def filter_tags(self, queryset):
        """Используется в filter_queryset """
        tags = self.request.query_params.getlist('tags')
        return queryset.filter(
            tags__slug__in=tags
        ).distinct()

    def filter_queryset(self, queryset):
        shop_cart = self.form.cleaned_data.get('is_in_shopping_cart')
        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)
            assert isinstance(queryset, models.QuerySet), (
                "Expected '%s.%s' to return a QuerySet, but got a %s instead."
                % (type(self).__name__, name, type(queryset).__name__)
            )

        if shop_cart == '1':
            return queryset
        return self.filter_tags(queryset)
