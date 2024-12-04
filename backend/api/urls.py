from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    RecipeViewSet,
    TagViewSet,
    IngredientViewSet,
    FollowViewSet,
    FavoriteViewSet,
    UserViewSet
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
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
