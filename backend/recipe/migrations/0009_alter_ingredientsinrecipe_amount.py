# Generated by Django 3.2.3 on 2024-11-30 14:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0008_auto_20241130_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientsinrecipe',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Количество ингредиентов не может быть меньше 1.'), django.core.validators.MaxValueValidator(10000, message='Количество ингредиентов не может быть больше 10000.')], verbose_name='Количество'),
        ),
    ]
