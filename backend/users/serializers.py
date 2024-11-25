import re
from rest_framework import serializers

from django.conf import settings
from foodgram_django.fields import Base64ImageField
from recipe.models import Follow
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
            'avatar'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'is_subscribed': {'read_only': True}}

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or not hasattr(request, 'user'):
            return False
        user = request.user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj).exists()
        return False

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url)
        return request.build_absolute_uri(
            f'{settings.MEDIA_URL}avatar-icon.png'
        )


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Use only letters, digits, ., @, +, and - characters.'
            )
        return value
