from django.contrib import admin
from django.contrib.auth.models import Group
from django.db import models
from django.forms import TextInput
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Tag, User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Класс представления модели пользователей."""
    list_display = (
        'email', 'id', 'username',
        'first_name', 'last_name', 'role'
    )
    search_fields = ('email', 'first_name')


@admin.register(Recipe)
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


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс представление инградиентов."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('^name',)


class TagAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'type': 'color'})},
    }


admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient)
admin.site.register(Ingredient, IngredientAdmin)
