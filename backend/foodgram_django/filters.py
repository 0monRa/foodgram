import django_filters
from recipe.models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags',
        to_field_name='id',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    author = django_filters.NumberFilter(field_name='author__id')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_in_shopping_cart', 'is_favorited']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            if value:
                return queryset.filter(shoppingcart__user=user)
            return queryset.exclude(shoppingcart__user=user)
        return queryset.none()

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            if value:
                return queryset.filter(favorite__user=user)
            return queryset.exclude(favorite__user=user)
        return queryset.none()
