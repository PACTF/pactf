from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from ctflex import models


class CompetitorInline(admin.StackedInline):
    model = models.Competitor
    can_delete = False
    verbose_name_plural = 'competitor'


class UserAdmin(BaseUserAdmin):
    inlines = (CompetitorInline,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        personal_info = self.fieldsets[1][1]  # mutable, so we can modify it in the next line
        personal_info['fields'] = tuple(field for field in personal_info['fields'] if field != 'email')


class TimerAdmin(admin.ModelAdmin):
    readonly_fields = ('end',)


class SubmissionAdmin(admin.ModelAdmin):
    readonly_fields = ('time',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(models.Team)

admin.site.register(models.CtfProblem)
admin.site.register(models.Solve)
admin.site.register(models.Submission)

admin.site.register(models.Timer, TimerAdmin)
admin.site.register(models.Window)
