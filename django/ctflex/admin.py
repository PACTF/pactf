"""Register models with the admin interface"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from ctflex import models
from ctflex import queries


# region Helpers

class AllFieldModelAdmin(admin.ModelAdmin):
    EXCLUDE = ('id',)
    INCLUDE = ()

    def __init__(self, model, admin_site):
        self.list_display = ([field.name for field in model._meta.fields
                              if field.name not in self.EXCLUDE] +
                             list(self.INCLUDE))
        super(AllFieldModelAdmin, self).__init__(model, admin_site)


# endregion

# region Admin Filters

class EligibileFilter(admin.SimpleListFilter):
    title = 'eligibility'
    parameter_name = 'eligible'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Eligible'),
            ('0', 'Ineligible'),
        )

    def queryset(self, request, queryset):
        if self.value() in ('0', '1'):
            result = [team.id for team in queryset
                      if queries.eligible(team)
                      == (self.value() == '1')]
            return queryset.filter(id__in=result)


# endregion


# region Admin Actions

def ban(modeladmin, request, queryset):
    for object in queryset:
        object.banned = True
        object.save()


def unban(modeladmin, request, queryset):
    for object in queryset:
        object.banned = False
        object.save()


# endregion


# region Admin Classes

class CompetitorInline(admin.StackedInline):
    model = models.Competitor
    can_delete = False
    verbose_name_plural = 'competitor'


class UserAdmin(BaseUserAdmin):
    inlines = (CompetitorInline,)
    date_hierarchy = 'date_joined'
    list_display = ('username', 'team', 'email', 'first_name', 'last_name', 'is_staff')

    def team(self, user):
        try:
            return user.competitor.team.name
        except ObjectDoesNotExist:
            return None

    def remove_email_field(self):
        # (`personal_info` is mutable, so we can modify it after getting a reference.)
        personal_info = self.fieldsets[1][1]
        personal_info['fields'] = tuple(field for field in personal_info['fields'] if field != 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_email_field()


class TeamAdmin(AllFieldModelAdmin):
    EXCLUDE = ('id', 'passphrase',)
    INCLUDE = ('size', 'eligible')
    date_hierarchy = 'created_at'
    actions = [ban, unban]
    list_filter = (EligibileFilter, 'banned',)
    inlines = (CompetitorInline,)
    search_fields = ('name', 'school')

    def eligible(self, team):
        return queries.eligible(team)

    eligible.boolean = True


class WindowAdmin(AllFieldModelAdmin):
    date_hierarchy = 'start'


class TimerAdmin(AllFieldModelAdmin):
    EXCLUDE = ()
    readonly_fields = ('end',)
    date_hierarchy = 'start'


class CtfProblemAdmin(AllFieldModelAdmin):
    EXCLUDE = ('id', 'description_raw', 'hint_raw', 'grader')
    search_fields = ('name', 'window__codename')
    list_filter = ('window',)


class SolveAdmin(AllFieldModelAdmin):
    EXCLUDE = ()
    date_hierarchy = 'date'
    search_fields = (
        'problem__name',
        'competitor__user__username',
        'competitor__team__name',
        'date',
        'flag',
    )


class SubmissionAdmin(AllFieldModelAdmin):
    EXCLUDE = ('id', 'p_id')
    date_hierarchy = 'date'
    readonly_fields = ('date',)
    list_display_links = ('date',)
    list_filter = ('correct',)
    search_fields = (
        'problem__name',
        'competitor__user__username',
        'competitor__team__name',
        'date',
        'flag',
    )


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'window')
    date_hierarchy = 'date'
    list_display_links = ('title',)
    filter_horizontal = ('competitors', 'problems')
    list_filter = ('window',)
    search_fields = (
        'title',
        'body',
    )


# endregion


# region Registration

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(models.Team, TeamAdmin)

admin.site.register(models.Window, WindowAdmin)
admin.site.register(models.Timer, TimerAdmin)

admin.site.register(models.CtfProblem, CtfProblemAdmin)
admin.site.register(models.Solve, SolveAdmin)
admin.site.register(models.Submission, SubmissionAdmin)

admin.site.register(models.Announcement, AnnouncementAdmin)

# endregion
