from django.contrib import admin
from .models import MyUser, TemporaryUser, Badges, UserBadge, KarmaTransaction

admin.site.register(MyUser)
admin.site.register(TemporaryUser)
admin.site.register(Badges)
admin.site.register(UserBadge)


@admin.register(KarmaTransaction)
class KarmaTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'reason', 'created_at')
    list_filter = ('created_at', 'amount')
    search_fields = ('user__username', 'user__email', 'reason')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


