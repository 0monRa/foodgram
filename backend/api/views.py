from django.shortcuts import render
from rest_framework import (
    viewsets,
    mixins
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from recipe.models import (
    Recipe,
    Tag,
    Ingredient,
    Favorite,
    Follow,
    ShoppingCart
)
from users.models import User
from .serializers import (
    RecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    FollowSerializer,
    ShoppingCartSerializer
)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    #permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    #permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    #permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def toggle_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response({'status': 'added to favorites'})
        elif request.method == 'DELETE':
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response({'status': 'removed from favorites'})


class ShoppingCartViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingCartSerializer
    #permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def toggle_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response({'status': 'added to shopping cart'})
        elif request.method == 'DELETE':
            ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            ).delete()
            return Response({'status': 'removed from shopping cart'})

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        items = ShoppingCart.objects.filter(
            user=request.user
        ).select_related('recipe')
        content = ""
        for item in items:
            for ingredient in item.recipe.ingredients.all():
                content += f"{ingredient.name} — {ingredient.amount} {ingredient.measurement_unit}\n"
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response
