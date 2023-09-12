from django.contrib.auth.models import AbstractUser
from django.db import models


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
        ordering = ['username']
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_author',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
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

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name