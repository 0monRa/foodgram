from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, views, filters
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer
from .permissions import AdministratorPermission, AuthenticatedPermission

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            self.permission_classes = [AllowAny]
        elif self.action in ['destroy', 'update', 'partial_update']:
            self.permission_classes = [AdministratorPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

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

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """Эндпоинт для смены пароля текущего пользователя."""
        user = request.user
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"detail": "Не указан новый пароль."},
                            status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Пароль успешно обновлен."},
                        status=status.HTTP_200_OK)


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
