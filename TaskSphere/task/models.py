from django.db import models
from django.contrib.auth import get_user_model
from dateutil.relativedelta import relativedelta

from user.services import award_karma_to_user

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

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    interval = models.PositiveIntegerField(default=1)
    next_occurance = models.DateTimeField()

    def calculate_next_occurrence(self):
        """
        Calculate and return the next occurrence based on frequency and interval.
        Does not save to database - call save() separately if needed.
        """
        if self.frequency == 'daily':
            self.next_occurance = self.next_occurance + relativedelta(days=self.interval)
        elif self.frequency == 'weekly':
            self.next_occurance = self.next_occurance + relativedelta(weeks=self.interval)
        elif self.frequency == 'monthly':
            self.next_occurance = self.next_occurance + relativedelta(months=self.interval)
        
        return self.next_occurance


class Task(models.Model):
        
        PRIORITY_CHOICES = [
                ('low', 'Low'),
                ('medium', 'Medium'),
                ('important', 'Important'),
                ('very_important', 'Very Important'),
                ('extremely_important', 'Extremely Important')
        ]

        user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
        title = models.CharField(max_length=40)
        description = models.TextField(blank=True, null=True)
        is_completed = models.BooleanField(default=False)
        priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
        due_date = models.DateTimeField(null=True, blank=True)
        reminder = models.DateTimeField(null=True, blank=True)
        expired = models.BooleanField(default=False)
        is_recurring = models.BooleanField(default=False)
        recurrence_rule = models.OneToOneField(RecurrenceRule, on_delete=models.SET_NULL, blank=True, null=True, related_name='task')
        category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
        tags = models.ManyToManyField(Tag, blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        parent_recurring_task = models.ForeignKey(
             'self',
             on_delete=models.CASCADE,
             null=True,
             blank=True,
             related_name='instances'
             )

        def calculate_subtasks_completion_percentage(self):
            total_subtasks = self.subtasks.count()
            
            if total_subtasks == 0:
                return 0
            
            completed_subtasks = self.subtasks.filter(is_completed=True).count()
            
            return round((completed_subtasks / total_subtasks) * 100)

        def check_all_subtasks_completion(self):
            total_subtasks = self.subtasks.count()

            if total_subtasks == 0:
                return False
            
            completed_subtasks = self.subtasks.filter(is_completed = True).count()

            if completed_subtasks == total_subtasks:
                return True
            return False

        def __str__(self):
             return self.title
        

class SubTask(models.Model):
     title = models.CharField(max_length=20)
     parent_task = models.ForeignKey(Task, related_name='subtasks', on_delete=models.CASCADE)
     is_completed = models.BooleanField(default=False)

     def __str__(self):
          return f'{self.parent_task.title} - {self.title}'
     







