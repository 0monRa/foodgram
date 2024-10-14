from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    title = models.CharField(
        max_length=256,
        verbose_name='Название рецепта'
    )
    '''image = models.ImageField(
        upload_to='media/',  # ???
        verbose_name='Изображение рецепта'
    )'''
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name='Ингредиенты'
    )
    tag = models.ManyToManyField(
        'Tag',
        verbose_name='Тег'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления'
    )


class Tag(models.Model):
    title = models.CharField(
        max_length=256,
        unique=True,
        verbose_name='Название тэга'
    )
    slug = models.SlugField(
        unique=True,
    )


class Ingredient(models.Model):
    title = models.CharField(
        max_length=256,
        unique=True,
        verbose_name='Название ингредиента'
    )
    unit_of_measure = models.CharField(
        max_length=256,
        verbose_name='Единица измерения'
    )
