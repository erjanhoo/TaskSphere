from django.urls import path
from .views import (
    CreateTaskView,
    ListTasksView,
    TaskDetailView,
    UpdateTaskView,
    DeleteTaskView,
    ToggleTaskCompletion,
    SubtaskToggleView,
    CalendarTasksView,
    CategoryListView,
    CategoryCreateView,
    CategoryDetailView,
    CategoryUpdateView,
    CategoryDeleteView,
    TagListView,
    TagCreateView,
    TagDetailView,
    TagUpdateView,
    TagDeleteView,
)

urlpatterns = [
    # Task CRUD
    path('create/', CreateTaskView.as_view(), name='create-task'),
    path('list/', ListTasksView.as_view(), name='list-tasks'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:pk>/update/', UpdateTaskView.as_view(), name='update-task'),
    path('<int:pk>/delete/', DeleteTaskView.as_view(), name='delete-task'),
    path('<int:pk>/toggle/', ToggleTaskCompletion.as_view(), name='toggle-task-completion'),
    path('calendar/', CalendarTasksView.as_view(), name='calendar-tasks'),
    
    # Subtasks
    path('subtask/<int:pk>/toggle/', SubtaskToggleView.as_view(), name='toggle-subtask'),
    
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
    
    # Tags
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('tags/create/', TagCreateView.as_view(), name='tag-create'),
    path('tags/<int:pk>/', TagDetailView.as_view(), name='tag-detail'),
    path('tags/<int:pk>/update/', TagUpdateView.as_view(), name='tag-update'),
    path('tags/<int:pk>/delete/', TagDeleteView.as_view(), name='tag-delete'),
]

