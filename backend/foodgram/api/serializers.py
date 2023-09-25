from api.validators import validate_username
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from foodgram import settings
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Subscription, Tag, User)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователей."""
    username = serializers.CharField(
        max_length=150,
        validators=[
            validate_username,
            UniqueValidator(queryset=User.objects.all())
        ]
    )
    first_name = serializers.CharField(
        max_length=150,
    )
    last_name = serializers.CharField(
        max_length=150,
    )
    is_subscribed = serializers.SerializerMethodField('get_subscribed')
    password = serializers.CharField(
        max_length=150,
        write_only=True
    )
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'password',
        ]
        lookup_field = 'username'

    def get_subscribed(self, obj):
        """Получение наличия в подписках"""
        user = self.context['request'].user
        if user.is_authenticated:
            return (Subscription.objects
                    .filter(user=user)
                    .filter(author=obj)
                    .exists())
        return False

    @transaction.atomic
    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        try:
            user.set_password(validated_data['password'])
            user.save()
        except KeyError:
            pass
        return user


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""
    new_password = serializers.CharField(
        max_length=150,
        write_only=True,
        required=True
    )
    current_password = serializers.CharField(
        max_length=150,
        write_only=True,
        required=True
    )

    @transaction.atomic
    def create(self, validated_data):
        user = self.instance
        user.set_password(validated_data['password'])
        user.save()
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate(self, data):
        user = self.instance
        try:
            _ = data['current_password']
        except KeyError:
            raise serializers.ValidationError(
                "Требуется поле current_password"
            )
        try:
            _ = data['new_password']
        except KeyError:
            raise serializers.ValidationError(
                "Требуется поле new_password"
            )
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError(
                "Неверно имя пользователя или пароль"
            )
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для инградиентов."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для инградиентов в рецепте."""
    id = serializers.SerializerMethodField('get_ingredient')
    name = serializers.SerializerMethodField('get_name')
    measurement_unit = serializers.SerializerMethodField(
        'get_measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'measurement_unit', 'amount']

    def get_ingredient(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class IngredientWriteField(serializers.RelatedField):
    """Поле для инградиента в сериализаторе записи рецепта."""
    def to_representation(self, value):
        """Функция получения значения из базы."""
        return value

    def to_internal_value(self, data):
        """Функция записи значения в базу."""
        try:
            ingredient = Ingredient.objects.get(id=data['id'])
        except ObjectDoesNotExist:
            raise serializers.ValidationError({'id': 'doesnt exists'})
        return RecipeIngredients.objects.create(
            ingredient=ingredient,
            amount=data['amount'],
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения рецептов."""
    tags = serializers.SlugRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        slug_field='id'
    )
    ingredients = IngredientWriteField(
        many=True,
        queryset=RecipeIngredients.objects.all(),
    )
    author = UserSerializer(required=False)
    image = Base64ImageField()

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data,
        )
        recipe.tags.set(tags)
        recipe.ingredients.set(ingredients)
        return recipe

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance=instance,
            context=self.context
        ).data

    class Meta:
        model = Recipe
        fields = '__all__'


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецептов."""
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    author = UserSerializer()
    image = serializers.SerializerMethodField('get_image')
    is_favorited = serializers.SerializerMethodField('get_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        'get_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        ]

    def get_favorited(self, obj):
        """Получение наличия в избранном"""
        user = self.context['request'].user
        if user.is_authenticated:
            return (Favorite.objects
                    .filter(user=user)
                    .filter(recipe=obj)
                    .exists())
        return False

    def get_shopping_cart(self, obj):
        """Получение наличия в корзине"""
        user = self.context['request'].user
        if user.is_authenticated:
            return (ShoppingCart.objects
                    .filter(user=user)
                    .filter(recipe=obj)
                    .exists())
        return False

    def get_image(self, obj):
        return f'{settings.MEDIA_URL}{obj.image}'


class FavoriteShoppingCartSerializer(serializers.BaseSerializer):
    """Сериализатор для избранного, списка покупок"""
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.name,
            'image': f'{settings.MEDIA_URL}{instance.image}',
            'cooking_time': instance.cooking_time
        }


class SubscribeSerializer(UserSerializer):
    """Расширенный сериализатор для подписок"""
    recipes = serializers.SerializerMethodField('get_recipes')
    recipes_count = serializers.SerializerMethodField('get_recipes_count')

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes',
            'recipes_count',
        ]

    def get_recipes(self, obj):
        """Получение рецептов"""
        limit = self.context['request'].query_params.get('recipes_limit')
        query = Recipe.objects.filter(author=obj)
        if limit is not None:
            query = query[:int(limit)]
        recipes = FavoriteShoppingCartSerializer(
            query,
            many=True,
        )
        return recipes.data

    def get_recipes_count(self, obj):
        """Получение количества рецептов"""
        return Recipe.objects.filter(author=obj).count()
