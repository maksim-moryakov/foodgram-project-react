from recipes.models import Favorite, Recipe, ShoppingCart, User
from rest_framework import filters


class RecipeQueryFilter(filters.BaseFilterBackend):
    """Фильт рецептов по url параметрам."""

    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.getlist('tags')
        author = request.query_params.get('author')
        if request.user.is_authenticated:
            user = User.objects.get(username=request.user)
        else:
            user = None
        favor = request.query_params.get('is_favorited')
        shop_cart = request.query_params.get('is_in_shopping_cart')

        if user and favor == '1':
            return (
                Recipe.objects
                .filter(id__in=Favorite.objects
                        .filter(user=user).values('recipe__id'))
                .filter(tags__slug__in=tags)
            )
        if user and shop_cart == '1':
            return (
                Recipe.objects
                .filter(id__in=ShoppingCart.objects
                        .filter(user=user).values('recipe__id'))
            )
        if author:
            return queryset.filter(
                tags__slug__in=tags, author=User.objects.get(id=author),
            )
        return queryset.filter(tags__slug__in=tags)
