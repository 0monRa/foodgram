# Generated by Django 3.2.3 on 2024-11-19 12:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0006_rename_title_ingredient_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipe',
            old_name='tag',
            new_name='tags',
        ),
    ]