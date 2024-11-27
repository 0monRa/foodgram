from rest_framework import serializers

from .fields import Base64ImageField
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

from users.serializers import UserSerializer

from django.conf import settings


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

    def save_recipe(self, validated_data, instance=None):
        ingredients_data = validated_data.pop('ingredient_in_recipe', [])
        tags_data = validated_data.pop('tags', [])

        if instance is None:
            instance = Recipe.objects.create(**validated_data)

        IngredientsInRecipe.objects.filter(recipe=instance).delete()
        for ingredient in ingredients_data:
            IngredientsInRecipe.objects.create(
                recipe=instance,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

        instance.tags.set(tags_data)

        return instance

    def create(self, validated_data):
        return self.save_recipe(validated_data)

    def update(self, instance, validated_data):
        return self.save_recipe(validated_data, instance)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags, many=True).data
        return representation

    def validate(self, data):
        ingredients = data.get('ingredient_in_recipe')
        unique_ingredients = set()
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
        for ingredient in ingredients:
            if ingredient['id'] in unique_ingredients:
                raise serializers.ValidationError(
                    {'ingredients': (
                        'Ингредиенты в рецепте не должны повторяться.'
                    )
                    }
                )
            unique_ingredients.add(ingredient['id'])
        return data

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше или равно 1.'
            )
        return value


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class FollowSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ('user', 'author')


class SubscriptionRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

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
            settings.PAG_PAGE_SIZE
        )
        recipes = Recipe.objects.filter(author=obj)
        if isinstance(recipes_limit, str) and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
        else:
            recipes_limit = settings.PAG_PAGE_SIZE
        recipes = recipes[:recipes_limit]
        serializer = SubscriptionRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
