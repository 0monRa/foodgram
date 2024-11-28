from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings


class User(AbstractUser):

    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

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
        default={settings.BASE_DIR} / '/static/media/userpic-icon.jpg',
    )
    is_subscribed = models.BooleanField(
        verbose_name='Подписка',
        default=False,
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    @property
    def is_user(self):
        return self.role == self.ROLE_USER

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def clean(self):
        if self._state.adding and self.is_superuser and self.is_admin:
            raise ValidationError('Суперпользователь — всегда администратор!')

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ROLE_ADMIN
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.username
