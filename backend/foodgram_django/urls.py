from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import RecipeViewSet, TagViewSet, IngredientViewSet

router = DefaultRouter()

router.register('tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
