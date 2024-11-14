from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import ValidationError
import re

from recipe.models import Follow, Recipe
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer для чтения / создания пользователя модели User.
    Переопределён метод create для возможности получения токена по
    кастомным url. - шифрование пароля по правилам djosera.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'is_subscribed': {'read_only': True}}

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Follow.objects.filter(user=user, author=obj).exists()
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('is_subscribed', None)
        return representation

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError("Username must be alphanumeric and can contain only letters, digits, ., @, +, and - characters.")
        return value

