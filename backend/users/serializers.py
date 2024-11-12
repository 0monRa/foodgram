from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

'''from api_yamdb.constants import (
    EMAIL_FIELD_LENGTH,
    USERNAME_FIELD_LENGTH,
)'''

UserModel = get_user_model()


class _BaseUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=128,
        required=False
    )

    def validate_username(self, value):
        UserModel.username_validator(value)
        if value == 'me':
            raise serializers.ValidationError(
                'Недопустимое имя пользователя!')
        return value


class UserSerializer(_BaseUserSerializer):
    email = serializers.EmailField(
        max_length=128,
        required=False
    )
    first_name = serializers.CharField(
        max_length=128,
        required=False
    )
    last_name = serializers.CharField(
        max_length=128,
        required=False
    )
    bio = serializers.CharField(
        max_length=None,
        required=False
    )

    class Meta:
        model = UserModel
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio'
        )


class AdminSerializer(UserSerializer):
    username = serializers.CharField(
        max_length=128,
        required=True
    )
    email = serializers.EmailField(
        max_length=128,
        required=True
    )
    role = serializers.ChoiceField(
        required=False,
        choices=UserModel.ROLE_CHOICES
    )

    class Meta:
        model = UserModel
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )

        validators = [
            UniqueTogetherValidator(
                queryset=UserModel.objects.all(),
                fields=('username', 'email')
            )
        ]


class SignupSerializer(_BaseUserSerializer):
    username = serializers.CharField(
        max_length=128,
        required=True
    )
    email = serializers.EmailField(
        max_length=128,
        required=True
    )

    class Meta:
        model = UserModel
        fields = ('username', 'email')

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        user = self._get_user(email=email)
        if user and user.username != username:
            raise serializers.ValidationError(
                'Email уже используется!')

        user = self._get_user(username=username)
        if user and user.email != email:
            raise serializers.ValidationError(
                'Имя пользователя уже используется!')

        return data

    def create(self, validated_data):
        user = self._get_user(**validated_data)
        if not user:
            user = UserModel.objects.create(**validated_data)
        return user

    @staticmethod
    def _get_user(**kwargs):
        user = UserModel.objects.filter(**kwargs)
        if user.exists():
            return user.first()
