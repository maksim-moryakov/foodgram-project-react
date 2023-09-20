import re

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F


class User(AbstractUser):
    """Модель пользователя."""
    USER = 'user'
    ADMIN = 'admin'
    ROLES = [
        (USER, 'Пользователь'),
        (ADMIN, 'Администратор'),
    ]
    role = models.CharField(
        choices=ROLES,
        default=USER,
        max_length=30,
        verbose_name='РОЛЬ'
    )

    @property
    def is_admin(self):
        return self.role == User.ADMIN

    class Meta:
        ordering =  ('username',)
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для подписок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~(F('user') == F('author')),
                name='user_cannot_subscribe_to_self'
            )
        ]
        verbose_name_plural = 'Подписки'


class Ingredient(models.Model):
    """Модель для инградиентов."""
    name = models.CharField('Название', max_length=100)
    measurement_unit = models.CharField(max_length=30, verbose_name='Ед. изм.')

    class Meta:
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецепта с инградиентами."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField()

    def clean(self):
        if self.amount <= 0:
            raise ValidationError('Количество должно быть больше нуля')

    def __str__(self):
        return self.ingredient.name


class Tag(models.Model):
    """Модель для тегов."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = 'Теги'

    def clean(self):
        if not re.match('^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', self.color):
            raise ValidationError('Невалидный хекс-код цвета')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        RecipeIngredient,
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        upload_to='recipes',
        verbose_name='Изображение блюда',
        help_text='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Заполните текстовое описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в мин.',
        help_text='Заполните время приготовления'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name_plural = 'Рецепты'

    def clean(self):
        if self.cooking_time <= 0:
            raise ValidationError('Время приготовления должно быть больше нуля')
        if self.cooking_time > 1440:
            raise ValidationError(
                'Время приготовления не может превышать 24 часа'
            )

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Рецепт'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name_plural = 'Списки покупок'


class Favorite(models.Model):
    """Модель избранных рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name_plural = 'Избранные рецепты'
