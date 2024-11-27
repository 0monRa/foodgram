# Generated by Django 3.2.3 on 2024-11-27 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_user_is_subscribed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('admin', 'Admin'), ('user', 'User'), ('superuser', 'Superuser')], default='user', max_length=50, verbose_name='Пользовательская роль'),
        ),
    ]
