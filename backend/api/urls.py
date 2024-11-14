from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, TagViewSet, IngredientViewSet
from users.views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]