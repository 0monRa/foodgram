from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    """Кастомизация админки для модели User."""
    model = User
    # Добавляем кастомные поля, если они есть
    fieldsets = DefaultUserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('role',)}),
    )

    # Настраиваем отображение в списке
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'role',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'role')
    ordering = ('id',)
