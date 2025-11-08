from rest_framework import serializers
from .models import Task, RecurrenceRule, SubTask, Category, Tag
from django.utils import timezone


class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = ('frequency', 'interval', 'next_occurance')


class CreateSubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = subTask
        fields = ('title',)

    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError('You must provide subtask name!')
        if len(value) < 3:
            raise serializers.ValidationError('Subtask name too short! Must be atleast 3 characters long')
        return value
    

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = subTask
        fields = ('__all__')


class CreateTaskSerializer(serializers.ModelSerializer):
    recurrence_rule = RecurrenceRuleSerializer(required=False)
    subtasks = CreateSubTaskSerializer(many=True, required=False)
    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'due_date', 'category', 'tags', 'recurrence_rule', 'is_recurring', 'subtasks', 'reminder')

    def validate_due_date(self, value):

        if value < timezone.now():
            raise serializers.ValidationError('Due date cannot be in the past!')
        return value
    
    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError('You must provide task name!')
        if len(value) < 3:
            raise serializers.ValidationError('Task name too short! Must be atleast 3 characters long')
        return value
    
    def validate_category(self, value):
        if value:
            user = self.context['request'].user
            if not Category.objects.filter(id=value.id, owner=user).exists():
                raise serializers.ValidationError('Category does not exist or does not belong to you')
        return value
    
    def validate_reminder(self,value):
        if value > self.due_date:
            raise serializers.ValidationError('Reminder can not be after due date!')
        return value
    
    def validate_tags(self, value):
        if value:
            user = self.context['request'].user
            for tag in value:
                if not Tag.objects.filter(id=tag.id, owner=user).exists():
                    raise serializers.ValidationError(f'Tag "{tag.name}" does not exist or does not belong to you')
        return value
        
    def create(self, validated_data):

        user = self.context['request'].user
        recurrence_data = validated_data.pop('recurrence_rule', None)
        subtasks_data = validated_data.pop('subtasks', [])
        task = Task.objects.create(user=user, **validated_data)

        if recurrence_data:
            if task.due_date:
                next_midnight = task.due_date.replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                recurrence_data['next_occurance'] = next_midnight
            recurrence = RecurrenceRule.objects.create(**recurrence_data)
            task.recurrence_rule = recurrence
            task.save()

        # Create multiple subtasks
        for subtask_data in subtasks_data:
            subTask.objects.create(
                title=subtask_data['title'],
                parent_task=task,
                is_completed=False
            )

        return task

    def update(self, instance, validated_data):
        recurrence_data = validated_data.pop('recurrence_rule', None)
        
        if recurrence_data:
            if instance.recurrence_rule:
                for key, value in recurrence_data.items():
                    setattr(instance.recurrence_rule, key, value)
                instance.recurrence_rule.save()
            else:
                instance.recurrence_rule = RecurrenceRule.objects.create(**recurrence_data)
        elif instance.recurrence_rule:
            instance.recurrence_rule.delete()
            instance.recurrence_rule = None
        
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        
        return instance


class TasksListSerializer(serializers.ModelSerializer):
    class Meta:
        subtasks_completion_percentage = serializers.SerializerMethodField()
        model = Task
        fields = ('id', 'title', 'priority','due_date', 'category', 'tags', 'created_at', 'updated_at', 'subtasks_completion_percentage')


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

    def get_subtasks_completion_percentage(self, obj):
        return obj.calculate_subtasks_completion_percentage()


class TaskUpdationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'is_recurring', 'tags', 'category', 'due_date')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

    def validate_name(self, value):
        if not value or len(value) < 3:
            raise serializers.ValidationError('Tag name must be atleast 3 characters long!')
        return value
        

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    def validate_name(self, value):
        if not value or len(value) < 3:
            raise serializers.ValidationError('Category name must be atleast 3 characters long!')
        return value
            