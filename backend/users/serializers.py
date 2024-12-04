import re
from rest_framework import serializers
from django.conf import settings

from api.fields import Base64ImageField
from recipe.models import Follow, Recipe
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)
    recipes_count = serializers.IntegerField(read_only=True)

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
            'avatar',
            'recipes_count',
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
            f'{settings.STATIC_URL}media/userpic-icon.2e3faa821bb5398be2c6.jpg'
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
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Use only letters, digits, ., @, +, and - characters.'
            )
        return value


class SubscriptionRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or not hasattr(request, 'user'):
            return False
        user = request.user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get(
            'recipes_limit',
            settings.PAGINATION_PAGE_SIZE
        )
        recipes = Recipe.objects.filter(author=obj)
        if isinstance(recipes_limit, str) and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
        else:
            recipes_limit = settings.PAGINATION_PAGE_SIZE
        recipes = recipes[:recipes_limit]
        serializer = SubscriptionRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        )
        return serializer.data
