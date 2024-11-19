from django_filters import rest_framework as filters
from recipe.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags',
        to_field_name='id',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['author', 'tags']
