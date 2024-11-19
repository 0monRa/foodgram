# Generated by Django 3.2.3 on 2024-11-12 12:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredientsinrecipe',
            options={},
        ),
        migrations.RemoveConstraint(
            model_name='ingredientsinrecipe',
            name='unique_ingredient',
        ),
        migrations.AlterUniqueTogether(
            name='ingredientsinrecipe',
            unique_together={('recipe', 'ingredient')},
        ),
    ]