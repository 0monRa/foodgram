from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework import filters, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import views, viewsets

#from api_yamdb.settings import EMAIL_HOST_USER

from .permissions import (
    AdministratorPermission,
    AuthenticatedPermission,
)
from .serializers import (
    AdminSerializer,
    SignupSerializer,
    UserSerializer,
)

UserModel = get_user_model()


@api_view(['POST'])
def auth_signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = default_token_generator.make_token(user)

        send_mail(
            subject='Confirmation Code',
            message=token,
            #from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def auth_token(request):
    username = request.data.get('username')
    confirmation_code = request.data.get('confirmation_code')

    if not username:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(UserModel, username=username)

    if default_token_generator.check_token(user, token=confirmation_code):
        refresh = RefreshToken.for_user(user)
        data = {'token': str(refresh.access_token)}
        return Response(data, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    lookup_field = 'username'
    serializer_class = AdminSerializer
    permission_classes = (AdministratorPermission,)
    pagination_class = PageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for key in ('username', 'email'):
            data = {key: serializer.validated_data.get(key)}
            user = UserModel.objects.filter(**data)
            if user.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        if request.method == 'PUT':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)


class MeViewSet(views.APIView):
    permission_classes = (AuthenticatedPermission,)

    def get(self, request):
        user = get_object_or_404(
            UserModel,
            username=request.user.username
        )
        serializer = AdminSerializer(user)
        self.check_object_permissions(request, user)
        return Response(serializer.data)

    def patch(self, request):
        user = get_object_or_404(
            UserModel,
            username=request.user.username
        )
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK)
