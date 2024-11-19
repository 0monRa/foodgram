from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, views, filters
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from api.paginations import CustomPageNumberPagination

from .serializers import UserSerializer, UserCreateSerializer
from .permissions import AdministratorPermission, AuthenticatedPermission

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination
    lookup_field = 'id'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    def get_queryset(self):
        return super().get_queryset()

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
        return UserSerializer

    def get_serializer_context(self):
        """Передаем контекст запроса в сериализатор."""
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        data = serializer.data
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Эндпоинт для получения данных текущего пользователя."""
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
            # Удаление аватара
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {"detail": "Оба поля 'current_password' и 'new_password' обязательны."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем текущий пароль
        if not user.check_password(current_password):
            return Response(
                {"detail": "Неверный текущий пароль."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Устанавливаем новый пароль
        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Пароль успешно обновлен."},
            status=status.HTTP_204_NO_CONTENT
        )


@api_view(['POST'])
def auth_token(request):
    """Эндпоинт для получения токена аутентификации."""
    email = request.data.get('email')
    password = request.data.get('password')
    user = get_object_or_404(User, email=email)

    if not user.check_password(password):
        return Response({"detail": "Неверные учетные данные."},
                        status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)
    return Response({'token': str(refresh.access_token)}, status=status.HTTP_200_OK)
