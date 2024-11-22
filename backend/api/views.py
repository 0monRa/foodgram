from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
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
from users.permissions import (
    IsOwnerOrAdminOrReadOnly,
)
from .serializers import (
    RecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    FollowSerializer,
)
from .paginations import CustomPageNumberPagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrAdminOrReadOnly
    ]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Только авторизованные пользователи могут создавать рецепты."}
            )
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[permissions.AllowAny]
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response(
            {"short-link": f"http://{request.get_host()}/api/recipes/{recipe.id}/"},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def add_to_shopping_cart(self, request, pk=None):
        """Добавление рецепта в корзину."""
        recipe = get_object_or_404(Recipe, id=pk)
        cart_item, created = ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response(
                {"detail": "Рецепт уже добавлен в корзину."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_data = {
            "id": recipe.id,
            "name": recipe.name,
            "image": request.build_absolute_uri(recipe.image.url),
            "cooking_time": recipe.cooking_time
        }
        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Удаление рецепта из корзины."""
        recipe = get_object_or_404(Recipe, id=pk)
        cart_item = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if not cart_item.exists():
            return Response(
                {"detail": "Рецепта нет в корзине."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart_item.delete()
        return Response(
            {"detail": "Рецепт удалён из корзины."},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.AllowAny]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        items = ShoppingCart.objects.filter(
            user=request.user
        ).select_related('recipe')
        
        if not items.exists():
            return Response(
                {"detail": "Корзина покупок пуста."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Словарь для агрегации ингредиентов
        ingredients = {}

        # Сбор данных из корзины
        for item in items:
            for ingredient_in_recipe in item.recipe.ingredient_in_recipe.all():
                ingredient = ingredient_in_recipe.ingredient
                amount = ingredient_in_recipe.amount
                if ingredient.name in ingredients:
                    ingredients[ingredient.name]['amount'] += amount
                else:
                    ingredients[ingredient.name] = {
                        'amount': amount,
                        'measurement_unit': ingredient.measurement_unit,
                    }

        # Формирование текста для файла
        content = "Список покупок:\n"
        for name, details in ingredients.items():
            content += f"{name} — {details['amount']} {details['measurement_unit']}\n"

        # Возвращаем файл
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response(
                {"detail": "Рецепт уже в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = {
            "id": recipe.id,
            "name": recipe.name,
            "image": request.build_absolute_uri(recipe.image.url),
            "cooking_time": recipe.cooking_time
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    # Удаление из избранного
    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удалить рецепт из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {"detail": "Рецепта нет в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(
            {"detail": "Рецепт удалён из избранного."},
            status=status.HTTP_204_NO_CONTENT
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
