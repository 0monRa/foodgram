from django.contrib import admin

from .models import Favorite, Follow, Ingredient, Recipe, ShoppingCart, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'favorites_count'
    )
    list_display_links = (
        'id',
        'name'
    )
    search_fields = (
        'name',
        'author__username',
        'author__email'
    )
    list_filter = ('tags',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'author'
        ).prefetch_related(
            'tags',
            'ingredients'
        )

    def tags_list(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())
    tags_list.short_description = 'Теги'

    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'Добавлено в избранное'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug'
    )
    list_display_links = (
        'id',
        'name',
        'slug'
    )
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    list_display_links = (
        'id',
        'name',
    )
    search_fields = ('name',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author'
    )
    list_filter = ('author',)
    search_fields = ('user',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'author')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe'
    )
    list_filter = ('user',)
    search_fields = ('user',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe'
    )
    list_filter = ('user',)
    search_fields = ('user',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')
