from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
    permissions,
    status,
    filters
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
from .permissions import (
    IsOwnerOrAdminOrReadOnly,
)
from .filters import RecipeFilter, IngredientFilter
from .paginations import CustomPageNumberPagination
from .permissions import AdministratorPermission
from .serializers import (
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    FollowSerializer,
    ShoppingCartSerializer,
    UserSerializer,
    UserCreateSerializer,
    SubscribeSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.annotate(
        recipes_count=Count('recipes')
    )
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination
    lookup_field = 'id'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    def get_queryset(self):
        queryset = User.objects.all()
        if self.action in ['subscriptions', 'subscribe']:
            queryset = queryset.annotate(
                recipes_count=Count('recipes')
            )
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        elif self.action in ['destroy', 'update', 'partial_update']:
            self.permission_classes = [AdministratorPermission]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['subscriptions', 'subscribe']:
            return SubscribeSerializer
        return UserSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'detail': 'Поле avatar обязательно для заполнения.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(
                user,
                data={'avatar': avatar_data},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': avatar_data},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {'detail': 'current_password и new_password обязательны.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(current_password):
            return Response(
                {'detail': 'Неверный текущий пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {'detail': 'Пароль успешно обновлен.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        user = request.user
        if request.method == 'POST':
            author = get_object_or_404(User, id=id)
            if user == author:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = {'user': user.id, 'author': author.id}
            serializer = FollowSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response_serializer = SubscribeSerializer(
                author,
                context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            author = get_object_or_404(User, id=id)
            deleted_count, _ = Follow.objects.filter(
                user=user,
                author=author
            ).delete()
            if deleted_count == 0:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {'detail': 'Вы успешно отписались.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(following__user=user)
        page = self.paginate_queryset(authors)

        if page is not None:
            serializer = SubscribeSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscribeSerializer(
            authors,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


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

        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        recipe_serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(
            recipe_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

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
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        recipe_serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

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
