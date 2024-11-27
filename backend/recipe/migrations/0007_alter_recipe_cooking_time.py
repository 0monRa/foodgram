# Generated by Django 3.2.3 on 2024-11-27 14:38

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0006_alter_shoppingcart_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Время приготовления должно быть не менее 1 минуты.')], verbose_name='Время приготовления'),
        ),
    ]
