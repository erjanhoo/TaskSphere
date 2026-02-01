from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache

from .serializers import (
    CreateTaskSerializer,
    TasksListSerializer,
    TaskDetailSerializer,
    CategorySerializer,
    TagSerializer
    )
from .models import Category, Tag, Task, SubTask
from .filters import TaskFilter

from user.services import award_karma_to_user


"""
Task CRUD Views
"""
class CreateTaskView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateTaskSerializer
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter
    
    def perform_create(self, serializer):
        """Override to invalidate cache after creating a task."""
        serializer.save()
        self._invalidate_task_cache()
    
    def _invalidate_task_cache(self):
        """Invalidate all task list caches for the current user."""
        user_id = self.request.user.id
        cache.delete(f'tasks_all_user_{user_id}')
        cache.delete(f'tasks_active_user_{user_id}')
        cache.delete(f'tasks_completed_user_{user_id}')
    
    
class ListTasksView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TasksListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter
    
    def get_queryset(self):
        """
        Return tasks for the current user.
        Excludes recurring task instances by default unless filtered.
        """
        return Task.objects.filter(
            user=self.request.user,
            parent_recurring_task__isnull=True
        ).select_related('category', 'recurrence_rule').prefetch_related('tags', 'subtasks')
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to implement caching for common filter patterns.
        Cache keys are based on user ID and filter parameters.
        """
        # Get filter parameters
        is_completed = request.query_params.get('is_completed', None)
        search = request.query_params.get('search', None)
        category = request.query_params.get('category', None)
        tag = request.query_params.get('tag', None)
        priority = request.query_params.get('priority', None)
        
        # Only cache if no complex filters (search, category, tag, priority)
        # Cache common cases: all tasks, active tasks, completed tasks
        should_cache = not any([search, category, tag, priority])
        
        if should_cache:
            # Generate cache key based on user and completion status
            if is_completed is None:
                cache_key = f'tasks_all_user_{request.user.id}'
            elif is_completed in ['true', 'True', '1', True]:
                cache_key = f'tasks_completed_user_{request.user.id}'
            else:
                cache_key = f'tasks_active_user_{request.user.id}'
            
            # Try to get from cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)
        
        # If not in cache or shouldn't cache, get from database
        response = super().list(request, *args, **kwargs)
        
        # Cache the response data for 5 minutes
        if should_cache and response.status_code == 200:
            cache.set(cache_key, response.data, timeout=300)  # 5 minutes
        
        return response



class TaskDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer


class UpdateTaskView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = CreateTaskSerializer
    
    def perform_update(self, serializer):
        """Override to invalidate cache after updating a task."""
        serializer.save()
        self._invalidate_task_cache()
    
    def _invalidate_task_cache(self):
        """Invalidate all task list caches for the current user."""
        user_id = self.request.user.id
        cache.delete(f'tasks_all_user_{user_id}')
        cache.delete(f'tasks_active_user_{user_id}')
        cache.delete(f'tasks_completed_user_{user_id}')


class ToggleTaskCompletion(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            task = Task.objects.get(id=pk, user=request.user)
        except Task.DoesNotExist:
            return Response({'error':'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Store previous state to determine if completing or uncompleting
        was_completed = task.is_completed
        task.is_completed = not task.is_completed
        task.save()

        karma_points = self.calculate_karma_for_task(task=task)
        
        if task.is_completed:
            # Task was just completed - award karma
            award_karma_to_user(request.user, karma_points, f'Task completed: {task.title}')
        else:
            # Task was uncompleted - deduct karma
            award_karma_to_user(request.user, -karma_points, f'Task uncompleted: {task.title}')

        # Invalidate profile cache
        cache_key = f'profile_info_user_{request.user.id}'
        cache.delete(cache_key)
        
        # Invalidate task list caches
        self._invalidate_task_cache(request.user.id)

        return Response({
            'message': f'Task is {"completed" if task.is_completed else "reopened"}',
            'karma_change': karma_points if task.is_completed else -karma_points
        })
    
    def _invalidate_task_cache(self, user_id):
        """Invalidate all task list caches for the given user."""
        cache.delete(f'tasks_all_user_{user_id}')
        cache.delete(f'tasks_active_user_{user_id}')
        cache.delete(f'tasks_completed_user_{user_id}')
    
    def calculate_karma_for_task(self, task):
        
        karma_map = {
            'low': 5,
            'medium': 10,
            'important': 15,
            'very_important': 20,
            'extremely_important': 25
        }
        return karma_map.get(task.priority, 10)


class DeleteTaskView(generics.DestroyAPIView):
    """
    Delete a task by ID.
    Automatically handles deletion of related RecurrenceRule due to CASCADE.
    """
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer  # Serializer required but not used for deletion
    
    def perform_destroy(self, instance):
        """Override to invalidate cache after deleting a task."""
        user_id = self.request.user.id
        instance.delete()
        self._invalidate_task_cache(user_id)
    
    def _invalidate_task_cache(self, user_id):
        """Invalidate all task list caches for the given user."""
        cache.delete(f'tasks_all_user_{user_id}')
        cache.delete(f'tasks_active_user_{user_id}')
        cache.delete(f'tasks_completed_user_{user_id}')


class CalendarTasksView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TasksListSerializer

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        return Task.objects.filter(
            user=self.request.user,
            due_date__gte=start_date,
            due_date__lte=end_date,
            is_recurring=False
        ).order_by('due_date')


"""
Subtasks CRUD Views
"""

class SubtaskToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        try:
            subtask = SubTask.objects.get(id=pk)
        except SubTask.DoesNotExist:
            return Response({'error':'Subtask not found'}, status=404)
        
        if subtask.parent_task.user != request.user:
            return Response({'error':'Not authorized'}, status=403)
        
        subtask.is_completed = not subtask.is_completed
        subtask.save()

        if subtask.is_completed:
            award_karma_to_user(user=subtask.parent_task.user, amount=5, reason='subtask completed')

        # Invalidate task list caches since subtask changes affect task list
        self._invalidate_task_cache(subtask.parent_task.user.id)

        if subtask.parent_task.check_all_subtasks_completion():
            award_karma_to_user(user=subtask.parent_task.user, amount=50, reason=f'All subtasks for {subtask.parent_task} has been completed')
        
        return Response({
            'id': subtask.id,
            'title': subtask.title,
            'is_completed': subtask.is_completed,
            'message': 'Subtask updated successfully'
        })
    
    def _invalidate_task_cache(self, user_id):
        """Invalidate all task list caches for the given user."""
        cache.delete(f'tasks_all_user_{user_id}')
        cache.delete(f'tasks_active_user_{user_id}')
        cache.delete(f'tasks_completed_user_{user_id}')
"""
Tags & Category CRUD Views
"""

class CategoryListView(generics.ListAPIView):
    """
    List all categories for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(owner=user)
    
class CategoryCreateView(generics.CreateAPIView):
    """
    Create a new category for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class CategoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific category by ID for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(owner=user)
    
class CategoryUpdateView(generics.UpdateAPIView):
    """
    Update a category by ID for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(owner=user)
    
class CategoryDeleteView(generics.DestroyAPIView):
    """
    Delete a category by ID for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(owner=user)
    
class TagDeleteView(generics.DestroyAPIView):
    """
    Delete a tag by ID for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def get_queryset(self):
        user = self.request.user
        return Tag.objects.filter(owner=user)
    
class TagUpdateView(generics.UpdateAPIView):
    """
    Update a tag by ID for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def get_queryset(self):
        user = self.request.user
        return Tag.objects.filter(owner=user)

class TagDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific tag by ID for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def get_queryset(self):
        user = self.request.user
        return Tag.objects.filter(owner=user)

class TagCreateView(generics.CreateAPIView):
    """
    Create a new tag for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
class TagListView(generics.ListAPIView):
    """
    List all tags for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def get_queryset(self):
        user = self.request.user
        return Tag.objects.filter(owner=user)

