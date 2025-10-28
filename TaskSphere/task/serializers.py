from rest_framework import serializers
from .models import Task, RecurrenceRule
from django.utils import timezone

class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = ('frequency', 'interval', 'next_occurance')


class CreateTaskSerializer(serializers.ModelSerializer):
    recurrence_rule = RecurrenceRuleSerializer(required=False)
    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'due_date', 'category', 'tags', 'recurrence_rule')

    def validate_due_date(self, value):

        if value and value < timezone.now():
            raise serializers.ValidationError('Due date cannot be in the past')
        return value
        
        
    def create(self, validated_data):

        user = self.context['request'].user
        recurrence_data = validated_data.pop('recurrence_rule', None)

        # Create recurrence rule if provided (removed is_recurring check since it's not in the serializer)
        if recurrence_data:
            recurrence = RecurrenceRule.objects.create(task=task, **recurrence_data)
        else:
            recurrence = None

        task = Task.objects.create(user=user, recurrence_rule=recurrence, **validated_data)
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
        model = Task
        fields = ('id', 'title', 'description', 'priority','due_date', 'category', 'tags', 'created_at', 'updated_at')


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


