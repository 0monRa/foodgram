from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models


class YaUser(AbstractUser):

    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
    )

    username = models.CharField(
        verbose_name='Логин',
        max_length=150,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    email = models.EmailField(
        verbose_name='email-адрес',
        unique=True
    )
    role = models.CharField(
        verbose_name='Пользовательская роль',
        choices=ROLE_CHOICES,
        default=ROLE_USER
    )

    @property
    def is_user(self):
        return self.role == self.ROLE_USER

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def clean(self):
        if self.is_superuser and self.is_admin:
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
