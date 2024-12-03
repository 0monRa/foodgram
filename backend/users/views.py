from django.db.models import Count
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)

from api.paginations import CustomPageNumberPagination
from api.serializers import FollowSerializer
from api.permissions import AdministratorPermission
from recipe.models import Follow

from .serializers import (
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
            self.permission_classes = [AllowAny]
        elif self.action in ['destroy', 'update', 'partial_update']:
            self.permission_classes = [AdministratorPermission]
        else:
            self.permission_classes = [IsAuthenticated]
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
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
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
        permission_classes=[IsAuthenticated]
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
        permission_classes=[IsAuthenticated],
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
        permission_classes=[IsAuthenticated]
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
