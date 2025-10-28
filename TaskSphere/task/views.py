from rest_framework import response
from rest_framework.views import APIView
from rest_framework import generics


from django_filters.rest_framework import DjangoFilterBackend


from .serializers import CreateTaskSerializer, TasksListSerializer, TaskDetailSerializer
from .models import Task
from .filters import TaskFilter


"""
Task CRUD Views
"""
class CreateTaskView(generics.CreateAPIView):
    serializer_class = CreateTaskSerializer
    queryset = Task
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter
    
    
class ListTasksView(generics.ListAPIView):
    queryset = Task.objects.filter(is_completed=False)
    serializer_class = TasksListSerializer


class TaskDetailView(generics.RetrieveAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer


class UpdateTaskView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = CreateTaskSerializer


class DeleteTaskView(generics.DestroyAPIView):
    """
    Delete a task by ID.
    Automatically handles deletion of related RecurrenceRule due to CASCADE.
    """
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer  # Serializer required but not used for deletion




