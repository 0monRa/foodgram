# Generated by Django 3.2.3 on 2024-12-06 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_user_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, default='/static/static/media/userpic-icon.jpg', null=True, upload_to='users/avatars/'),
        ),
    ]