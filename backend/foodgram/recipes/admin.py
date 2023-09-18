from django.contrib import admin
from django.contrib.auth.models import Group
from recipes.models import Favorite, Ingredient, Recipe, Tag, User


class UserAdmin(admin.ModelAdmin):
    """Класс представления модели пользователей."""
    list_display = (
        'email', 'id', 'username',
        'first_name', 'last_name', 'role'
    )
    search_fields = ('email', 'first_name')


class RecipeAdmin(admin.ModelAdmin):
    """Класс представления модели рецептов"""
    list_display = ('name', 'author')
    search_fields = ('name', 'tags__name', 'author__first_name')
    fields = (
        'tags', 'author', 'ingredients', 'name',
        'image', 'text', 'cooking_time', 'favorite',
    )
    readonly_fields = ('favorite',)

    def favorite(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


class IngredientAdmin(admin.ModelAdmin):
    """Класс представление инградиентов."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('^name',)


admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
