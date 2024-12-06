from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    model = User
    fieldsets = DefaultUserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('role',)}),
    )

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
    list_display_links = (
        'id',
        'username',
        'email',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'role')
    ordering = ('id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related()
