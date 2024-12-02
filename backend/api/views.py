from io import BytesIO

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
    permissions,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
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
from .filters import RecipeFilter, IngredientFilter
from .paginations import CustomPageNumberPagination
from .serializers import (
    RecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    FollowSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'tags',
        'ingredients'
    )
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrAdminOrReadOnly
    ]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
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
            {
                'short-link': (
                    f'http://{request.get_host()}/recipes/{recipe.id}/'
                )
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def add_to_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        cart_item, created = ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже добавлен в корзину.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': request.build_absolute_uri(recipe.image.url),
            'cooking_time': recipe.cooking_time
        }
        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        deleted_count = ShoppingCart.objects.filter(
            user=request.user,
            recipe_id=pk
        ).delete()[0]

        if deleted_count == 0:
            return Response(
                {'detail': 'Рецепта нет в корзине или он не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'detail': 'Рецепт удалён из корзины.'},
            status=status.HTTP_204_NO_CONTENT
        )

    def generate_shopping_list(self, user):
        ingredients = (
            Ingredient.objects.filter(
                recipes__in_shopping_carts__user=user
            ).values(
                'name',
                'measurement_unit'
            ).annotate(
                total_amount=Sum('ingredients_list__amount')
            ).order_by('name')
        )

        if not ingredients.exists():
            return None, 'Корзина покупок пуста.'

        content = 'Список покупок:\n'
        for ingredient in ingredients:
            content += (
                f'{ingredient["name"]} — {ingredient["total_amount"]} '
                f'{ingredient["measurement_unit"]}\n'
            )

        buffer = BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        return buffer, None

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.AllowAny]
    )
    def download_shopping_cart(self, request):
        buffer, error = self.generate_shopping_list(request.user)
        if error:
            return Response(
                {'detail': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = HttpResponse(buffer, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': request.build_absolute_uri(recipe.image.url),
            'cooking_time': recipe.cooking_time
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        deleted_count = Favorite.objects.filter(
            user=request.user,
            recipe_id=pk
        ).delete()[0]

        if deleted_count == 0:
            return Response(
                {'detail': 'Рецепта нет в избранном или он не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'detail': 'Рецепт удалён из избранного.'},
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
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user).select_related(
            'author'
        ).annotate(
            recipes_count=Count('author__recipes')
        )

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
            serializer = FavoriteSerializer(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'status': 'Рецепт добавлен в избранное'},
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            deleted_count, _ = Favorite.objects.filter(
                user=request.user,
                recipe=recipe
            ).delete()
            if deleted_count == 0:
                return Response(
                    {'detail': 'Рецепт не был в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'status': 'Рецепт удален из избранного'},
                status=status.HTTP_204_NO_CONTENT
            )
