from django.contrib import admin

from .models import Recipe, Tag, Ingredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'favorites_count'
    )
    search_fields = (
        'name',
        'author__username',
        'author__email'
    )
    list_filter = ('tags',)
    ordering = ('id',)

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
    search_fields = ('name',)
    ordering = ('id',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)
    ordering = ('id',)
