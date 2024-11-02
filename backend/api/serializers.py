from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from recipe.models import (
    Recipe,
    Ingredient,
    Tag,
    IngredientRecipe,
    ShoppingCart,
    Favorite
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = '__all__',
