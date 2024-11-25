from django.contrib import admin
from django import forms
from .models import User


class UserChangeForm(forms.ModelForm):
    password = forms.CharField(
        label="Новый пароль",
        required=False,
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'is_staff',
            'is_active',
            'role',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserChangeForm
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
    )
    search_fields = (
        'username',
        'email'
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active'
    )
    ordering = ('id',)
