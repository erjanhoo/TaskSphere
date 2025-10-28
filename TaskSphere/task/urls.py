from django.urls import path
from .views import (
    CreateTaskView,
    ListTasksView,
    TaskDetailView,
    UpdateTaskView,
    DeleteTaskView
)

urlpatterns = [
    path('create/', CreateTaskView.as_view(), name='create-task'),
    path('list/', ListTasksView.as_view(), name='list-tasks'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:pk>/update/', UpdateTaskView.as_view(), name='update-task'),
    path('<int:pk>/delete/', DeleteTaskView.as_view(), name='delete-task'),
]
