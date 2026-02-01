import django_filters
from django.db.models import Q
from .models import Task


class TaskFilter(django_filters.FilterSet):
    # Search by title (starts with or contains)
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Filter by completion status
    is_completed = django_filters.BooleanFilter(field_name='is_completed', label='Completed')
    
    # Filter by overdue status
    is_overdue = django_filters.BooleanFilter(method='filter_overdue', label='Overdue')
    
    # Filter by priority
    priority = django_filters.ChoiceFilter(
        field_name='priority',
        choices=Task.PRIORITY_CHOICES,
        label='Priority'
    )
    
    # Filter by category
    category = django_filters.NumberFilter(field_name='category__id', label='Category')
    
    # Filter by tags
    tag = django_filters.NumberFilter(field_name='tags__id', label='Tag')
    
    # Filter by due date
    due_date = django_filters.DateFilter(field_name='due_date__date', label='Due Date')
    due_date_before = django_filters.DateFilter(field_name='due_date__date', lookup_expr='lte', label='Due Before')
    due_date_after = django_filters.DateFilter(field_name='due_date__date', lookup_expr='gte', label='Due After')
    
    # Order by
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('due_date', 'due_date'),
            ('priority', 'priority'),
            ('title', 'title'),
        )
    )
    
    class Meta:
        model = Task
        fields = ['search', 'is_completed', 'is_overdue', 'priority', 'category', 'tag', 'due_date']
    
    def filter_search(self, queryset, name, value):
        """
        Search tasks by title.
        Returns tasks where title starts with the search value or contains it.
        """
        if not value:
            return queryset
        
        # starts with OR contains the value
        return queryset.filter(
            Q(title__istartswith=value) | Q(title__icontains=value)
        ).distinct()
    
    def filter_overdue(self, queryset, name, value):
        """
        Filter tasks that are overdue (past due date and not completed).
        """
        from django.utils import timezone
        
        if value:  # is_overdue=true
            return queryset.filter(
                due_date__lt=timezone.now(),
                is_completed=False
            )
        else:  # is_overdue=false
            return queryset.filter(
                Q(due_date__gte=timezone.now()) | Q(due_date__isnull=True) | Q(is_completed=True)
            )
    
    def filter_overdue(self, queryset, name, value):
        """
        Filter tasks that are overdue (past due date and not completed).
        """
        from django.utils import timezone
        
        if value:  # is_overdue=true
            return queryset.filter(
                due_date__lt=timezone.now(),
                is_completed=False
            )
        else:  # is_overdue=false
            return queryset.filter(
                Q(due_date__gte=timezone.now()) | Q(due_date__isnull=True) | Q(is_completed=True)
            )

