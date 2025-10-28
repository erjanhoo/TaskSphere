from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    

class RecurrenceRule(models.Model):
    FREQUENCY_CHOICES = [
         ('daily', 'Daily'),
         ('weekly', 'Weekly'),
         ('monthly', 'Monthly')
    ]

    task = models.ForeignKey('Task', related_name='recurrence', on_delete=models.CASCADE)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    interval = models.PositiveIntegerField(default=1)
    next_occurance = models.DateTimeField()


class Task(models.Model):
        
        PRIORITY_CHOICES = [
                ('low', 'Low'),
                ('medium', 'Medium'),
                ('important', 'Important'),
                ('very_important', 'Very Important'),
                ('extremely_important', 'Extremely Important')
        ]

        title = models.CharField(max_length=40)
        description = models.TextField(blank=True, null=True)
        is_completed = models.BooleanField(default=False)
        priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
        due_date = models.DateTimeField(null=True, blank=True)
        is_recurring = models.BooleanField(default=False)
        recurrence_rule = models.OneToOneField(RecurrenceRule, on_delete=models.SET_NULL, blank=True, null=True, related_name='task')
        category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
        tags = models.ManyToManyField(Tag, on_delete=models.SET_NULL, null=True, blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now_add=True)


        def __str__(self):
             return self.title

class SubTask(models.Model):
     title = models.CharField(max_length=20)
     parent_task = models.ForeignKey(Task, related_name='subtask', on_delete=models.CASCADE)
     status = models.BooleanField(default=False)

     def __str__(self):
          return f'{self.parent_task.title} - {self.title}'
     





