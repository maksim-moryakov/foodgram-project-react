from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Модель для пользователей."""
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

    class Meta:
        ordering = ('username',)
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == User.ADMIN


class Subscription(models.Model):
    """Модель для подписок на авторов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='publisher',
        verbose_name='Автор'
    )

    class Meta:
        models.UniqueConstraint(
            fields=['user', 'author'],
            name='unique_subscription'
        )


class Ingredient(models.Model):
    """Модель для инградиентов."""
    name = models.CharField('Название', max_length=100)
    measurement_unit = models.CharField(max_length=30, verbose_name='Ед. изм.')

    class Meta:
        verbose_name_plural = 'Инградиенты'

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """Модель связи рецепта с инградиентами."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.DO_NOTHING
    )
    amount = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.ingredient.name


class Tag(models.Model):
    """Модель для тегов."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""
    tags = models.ManyToManyField(
        Tag,
        related_name='recipe_tags',
        verbose_name='Теги'
    )
    author = models.ForeignKey(
        User,
        related_name='recipe_author',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    ingredients = models.ManyToManyField(
        RecipeIngredients,
        related_name='recipe_ingredients',
        verbose_name='Инградиенты'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes',
        verbose_name='Изображение блюда',
        help_text='Картинка, закодированная в Base64'
    )
    text = models.TextField(
        verbose_name='Текстовое описание',
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

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    """Модель списков покупок."""
    user = models.ForeignKey(
        User,
        related_name='owner',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppingcart',
        verbose_name='Рецепт'
    )

    class Meta:
        models.UniqueConstraint(
            fields=('user', 'recipe'),
            name='unique_shopping_cart'
        )


class Favorite(models.Model):
    """Модель избранных рецептов пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reader',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт'
    )

    class Meta:
        models.UniqueConstraint(
            fields=('user', 'recipe'),
            name='unique_favorite'
        )
