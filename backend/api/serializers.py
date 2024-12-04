import re

from rest_framework import serializers, validators
from django.conf import settings

from recipe.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientsInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import User

from .fields import Base64ImageField


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
            f'{settings.STATIC_URL}static/media/userpic-icon.jpg',
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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientsInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.'
            )
        return value


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsInRecipeSerializer(
        many=True,
        source='ingredient_in_recipe',
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
            'image',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False

    def save_recipe(self, instance, ingredients_data, tags_data):
        IngredientsInRecipe.objects.filter(recipe=instance).delete()
        for ingredient in ingredients_data:
            IngredientsInRecipe.objects.create(
                recipe=instance,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

        instance.tags.set(tags_data)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredient_in_recipe', [])
        tags_data = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self.save_recipe(recipe, ingredients_data, tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredient_in_recipe', [])
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        self.save_recipe(instance, ingredients_data, tags_data)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags, many=True).data
        return representation

    def validate(self, data):
        ingredients = data.get('ingredient_in_recipe')
        tags = data.get('tags', [])
        unique_tags = set(tags)
        if len(tags) != len(unique_tags):
            raise serializers.ValidationError(
                {
                    'tags': 'Теги не должны повторяться.'
                }
            )
        if not tags:
            raise serializers.ValidationError(
                {
                    'tags': 'Поле \'tags\' не может быть пустым.'
                }
            )
        if not ingredients:
            raise serializers.ValidationError(
                {
                    'ingredients': 'Список ингредиентов не может быть пустым.'
                }
            )
        unique_ingredient_ids = {
            ingredient['id'] for ingredient in ingredients
        }
        if len(unique_ingredient_ids) != len(ingredients):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты в рецепте не должны повторяться.'}
            )
        return data

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше или равно 1.'
            )
        return value


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже в избранном.'}
            )
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже добавлен в избарнное.'
            )
        ]


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ('user', 'author')


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='recipe.id',
        read_only=True
    )
    name = serializers.CharField(
        source='recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже добавлен в корзину.'
            )
        ]
