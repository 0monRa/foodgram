from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):

    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
    )

    username_validator = RegexValidator(
        regex=r'^[\w.@+-]+$',
        message='Use only contain @, ., +, and - characters.'
    )

    username = models.TextField(
        max_length=150,
        unique=True,
        verbose_name='Логин',
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='email-адрес',
    )
    password = models.CharField(
        max_length=128,
        verbose_name='Пароль'
    )
    role = models.CharField(
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        max_length=50,
        verbose_name='Пользовательская роль',
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        default='users/avatars/default_avatar.jpg',
    )

    @property
    def is_user(self):
        return self.role == self.ROLE_USER

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def clean(self):
        if self._state.adding and self.is_superuser and self.is_admin:
            raise ValidationError('Суперпользователь — всегда администратор!')

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ROLE_ADMIN
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
