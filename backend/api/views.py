from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet

from recipe.models import (
    Recipe,
    Tag,
    Ingredient,
    # User, - для него есть отдельное приложение
)
from .serializers import (
    TagSerializer
)


class RecipeViewSet(ModelViewSet):
    pass


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )


class IngredientViewSet(ModelViewSet):
    pass
