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


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(models.Team)

admin.site.register(models.CtfProblem)
admin.site.register(models.Solve)
admin.site.register(models.Submission)

admin.site.register(models.Timer)
admin.site.register(models.Window)