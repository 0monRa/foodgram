from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from .views import (
    RecipeViewSet,
    TagViewSet,
    IngredientViewSet,
    FollowViewSet,
    FavoriteViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet)
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'follows', FollowViewSet, basename='follows')
router.register(r'favorites', FavoriteViewSet, basename='favorites')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]