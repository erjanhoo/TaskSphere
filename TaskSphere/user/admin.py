from django.contrib import admin
from .models import MyUser, TemporaryUser

admin.site.register(MyUser)
admin.site.register(TemporaryUser)

