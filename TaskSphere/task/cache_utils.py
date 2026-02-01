"""
Utility functions for task caching management.
"""
from django.core.cache import cache
from django_redis import get_redis_connection

from .serializers import TasksListSerializer


def invalidate_user_task_cache(user_id):
    """
    Invalidate all task list caches for a specific user.
    Call this function whenever a task-related change occurs.
    
    Args:
        user_id: The ID of the user whose cache should be invalidated
    """
    cache_keys = [
        f'tasks_all_user_{user_id}',
        f'tasks_active_user_{user_id}',
        f'tasks_completed_user_{user_id}'
    ]
    cache.delete_many(cache_keys)


def get_cache_stats():
    """
    Get cache statistics for monitoring performance.
    Useful for debugging and monitoring cache effectiveness.
    
    Returns:
        dict: Cache statistics if available
    """
    try:
        # This works with django-redis
        redis_conn = get_redis_connection("default")
        info = redis_conn.info()
        
        return {
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
            'used_memory': info.get('used_memory_human', 'N/A'),
            'connected_clients': info.get('connected_clients', 0),
        }
    except Exception as e:
        return {'error': str(e)}


def warm_cache_for_user(user, task_queryset):
    """
    Pre-populate cache with task data for a user.
    Useful after bulk operations or login.
    
    Args:
        user: The user object
        task_queryset: QuerySet of tasks (should already be filtered for the user)
    """
    
    
    # Get all tasks
    all_tasks_data = TasksListSerializer(task_queryset, many=True).data
    cache.set(f'tasks_all_user_{user.id}', all_tasks_data, timeout=300)
    
    # Get active tasks
    active_tasks = [task for task in all_tasks_data if not task.get('is_completed')]
    cache.set(f'tasks_active_user_{user.id}', active_tasks, timeout=300)
    
    # Get completed tasks
    completed_tasks = [task for task in all_tasks_data if task.get('is_completed')]
    cache.set(f'tasks_completed_user_{user.id}', completed_tasks, timeout=300)


def clear_all_task_caches():
    """
    Clear all task-related caches.
    Use with caution - this will clear all users' task caches.
    Useful for maintenance or after major data migrations.
    """
    try:
        
        redis_conn = get_redis_connection("default")
        
        # Delete all keys matching task cache patterns
        for pattern in ['tasks_all_user_*', 'tasks_active_user_*', 'tasks_completed_user_*']:
            keys = redis_conn.keys(pattern)
            if keys:
                redis_conn.delete(*keys)
        
        return True
    except Exception as e:
        return False
