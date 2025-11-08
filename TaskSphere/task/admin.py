from django.contrib import admin
from .models import Task, Category, Tag, RecurrenceRule, subTask
    
# Register your models here.
admin.site.register(Task)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(subTask)
admin.site.register(RecurrenceRule)
