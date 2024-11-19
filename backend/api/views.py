from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
    mixins,
    permissions,
    status,
    serializers
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from foodgram_django.filters import RecipeFilter
from recipe.models import (
    Recipe,
    Tag,
    Ingredient,
    Favorite,
    Follow,
    ShoppingCart
)
from users.models import User
from users.permissions import (
    IsAdminOrReadOnly,
    IsOwnerOrAdminOrReadOnly,
)
from .serializers import (
    RecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    FollowSerializer,
    ShoppingCartSerializer
)
from .paginations import CustomPageNumberPagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly,]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Только авторизованные пользователи могут создавать рецепты."}
            )
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link', permission_classes=[permissions.AllowAny])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response(
            {"short-link": f"http://{request.get_host()}/api/recipes/{recipe.id}/"},
            status=status.HTTP_200_OK
        )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny, )
    http_method_names = ['get', 'head', 'options']


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ['get', 'head', 'options']
    permission_classes = (permissions.AllowAny, )


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def toggle_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response({'status': 'added to shopping cart'})
        elif request.method == 'DELETE':
            ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
            return Response({'status': 'removed from shopping cart'})

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        items = ShoppingCart.objects.filter(user=request.user).select_related('recipe')
        content = ""
        for item in items:
            for ingredient in item.recipe.ingredients.all():
                content += f"{ingredient.name} — {ingredient.amount} {ingredient.measurement_unit}\n"
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response
