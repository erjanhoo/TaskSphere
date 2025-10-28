import django_filters
from .models import Task

class TaskFilter(django_filters.FilterSet):
    status = django_filters.BooleanFilter('status', lookup_expr='exact')
    priority = django_filters.CharFilter('priority', lookup_expr='iexact')
    due_date_before = django_filters.DateTimeFilter('due_date', lookup_expr='lte')
    due_date_after = django_filters.DateTimeFilter('due_date', lookup_expr='gte')
    category = django_filters.CharFilter('category__name', lookup_expr='iexact')
    tag = django_filters.CharFilter('tags__name', lookup_expr='iexact')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'due_date_before', 'due_date_after', 'category', 'tag']