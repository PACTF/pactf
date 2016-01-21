import re
import uuid
from os.path import join
import importlib.machinery

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group, Permission
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.postgres import fields as psql

import markdown2


# TODO(Yatharth): Write decorator to set dispatch_uid automatically
# TODO(Yatharth): Write helper so error of clean returns all validationerrors


@receiver(pre_save, dispatch_uid='ctf.pre_save_validate')
def pre_save_validate(sender, instance, *args, **kwargs):
    # validate only fixtures (`loaddata` causes `raw` to be True)"""
    # if kwargs.get('raw', False):
    instance.full_clean()


# region User Models (by wrapping)

class Team(models.Model):

    # Essential data
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True)
    score = models.IntegerField(default=0)

    # Extra data
    school = models.CharField(max_length=40, blank=True, default='None')

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)

    def timer(self, window=None):
        if window is None:
            window = Window.current()
        return Timer.objects.get(window=window, team=self)

    def has_timer(self, window=None):
        try:
            self.timer(window=window)
        except Timer.DoesNotExist:
            return False
        else:
            return True

    def has_active_timer(self):
        return self.has_timer() and self.timer().active()

    def can_view_problems(self, window=None):
        return self.has_timer(window=window) and self.timer(window=window).start <= timezone.now()

    def start_timer(self):
        assert not self.has_timer()

        timer = Timer(window=Window.current(), team=self)
        timer.save()


class Competitor(models.Model):
    """Represents a competitor 'profile'

    Django's User class's fields are shunned except for:

        username, password, is_active, is_staff, date_joined

    """

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.PROTECT)

    # Shunned fields
    first_name = models.CharField("First name", max_length=30, blank=True)
    last_name = models.CharField("Last name", max_length=30, blank=True)
    email = models.EmailField("Email", unique=True)

    def __str__(self):
        return "<Competitor #{} {!r}>".format(self.id, self.user.username)


# endregion


# region Problem Models

# FIXME(Yatharth): Consider simplifying
class CtfProblem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)

    points = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    description_html = models.TextField(editable=False)
    hint = models.TextField(default='')
    hint_html = models.TextField(editable=False, blank=True, null=True)

    grader = models.FilePathField(
        help_text="Basename of the grading script from PROBLEM_DIR",
        path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$'
    )
    dynamic = models.FilePathField(
        help_text="Basename of the generator script in PROBLEM_DIR",
        path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$',
        blank=True, null=True
    )
    # dict function instead of {} because of mutability
    deps = psql.JSONField(default=dict, blank=True)

    def __str__(self):
        return "<Problem #{} {!r}>".format(self.id, self.name)

    def grade(self, flag, team):
        if not flag:
            return False, "Empty flag"

        grader_path = join(settings.PROBLEMS_DIR, self.grader)
        # FIXME(Yatharth): Handle FileNotFound
        grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()
        correct, message = grader.grade(team, flag)
        return correct, message

    # TODO(Cam): Markdown's safe_mode is deprecated; research safety
    @staticmethod
    def markdown_to_html(markdown):
        EXTRAS = ('fenced-code-blocks', 'smarty-pants', 'spoiler')

        html = markdown2.markdown(markdown, extras=EXTRAS, safe_mode='escape')
        return html

    def link_static(self, old_text):
        PATTERN = re.compile(r'''{% \s* ctfstatic \s+ (['"]) (?P<basename> (?:(?!\1).)+ ) \1 \s* (%})''', re.VERBOSE)
        REPLACEMENT = r'{}/{}/{{}}'.format(settings.PROBLEMS_STATIC_URL, self.id)
        REPLACER = lambda match: static(REPLACEMENT.format(match.group('basename')))

        new_text = PATTERN.sub(REPLACER, old_text)
        return new_text

    def process_html(self, html):
        return self.markdown_to_html(self.link_static(html))

    def clean(self):
        if not self.dynamic:
            if not self.description:
                raise ValidationError('Description must be provided for non-dynamic problems!')
            self.description_html = self.process_html(self.description)
        elif self.description:
            raise ValidationError('Description should be blank for dynamic problems')
        self.hint_html = self.process_html(self.hint)

    def generate_desc(self, team):
        if not self.dynamic:
            return self.description_html
        gen_path = join(settings.PROBLEMS_DIR, self.dynamic)
        gen = importlib.machinery.SourceFileLoader('gen', gen_path).load_module()
        desc = gen.generate(team)
        return self.process_html(desc)

class Submission(models.Model):
    """Records a flag submission attempt

    The `p_id` field exists in addition to the `problem` foreign key.
    This is so in order to handle deletion of problems while not deleting Submissions for historical reasons.
    This is not done with competitor and team as 1) IDs are less useful for deleted objects of such types and 2) they are linked with Users, which have an is_active property which is used instead of deletion.

    `team` exists for quick querying of whether someone in a particular competitor's team has solved a particular problem.
    """
    id = models.AutoField(primary_key=True)

    p_id = models.UUIDField()
    problem = models.ForeignKey(CtfProblem, on_delete=models.SET_NULL, null=True)
    competitor = models.ForeignKey(Competitor, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    time = models.DateTimeField(auto_now_add=True)
    flag = models.CharField(max_length=80)
    correct = models.NullBooleanField()

    def __str__(self):
        return "<Submission @{} problem={} competitor={}>".format(self.time, self.problem, self.competitor)

    def sync_problem(self):
        try:
            self.problem = CtfProblem.objects.get(pk=self.p_id)
        except CtfProblem.DoesNotExist:
            pass

    def sync_team(self):
        self.team = self.competitor.team

    def clean(self):
        self.sync_problem()
        self.sync_team()


# endregion


# region Config Models

# TODO: Consider dbsettings

# class SingletonModel(models.Model):
#     id = models.AutoField
#
#     class Meta:
#         abstract = True
#
#     def save(self, *args, **kwargs):
#         self.__class__.objects.exclude(id=self.id).delete()
#         super(SingletonModel, self).save(*args, **kwargs)
#
#     @classmethod
#     def load(cls):
#         try:
#             return cls.objects.get()
#         except cls.DoesNotExist:
#             return cls()
#
# class Config():
#     passs

# endregion


# region Timer Models

print_time = lambda time: time.astimezone(tz=None).strftime('%m-%d@%H:%M:%S')


class Window(models.Model):
    id = models.AutoField(primary_key=True)

    start = models.DateTimeField()
    end = models.DateTimeField()

    personal_timer_duration = models.DurationField()

    def __str__(self):
        return "<Window #{} {} – {}>".format(self.id, print_time(self.start), print_time(self.end))

    @staticmethod
    def active():
        try:
            Window.current()
        except Window.DoesNotExist:
            return False
        else:
            return True

    @staticmethod
    def current():
        now = timezone.now()
        return Window.objects.get(start__lte=now, end__gte=now)

    def validate_windows_dont_overlap(self):
        for window in Window.objects.exclude(id=self.id):
            if window.start <= self.end and self.start <= window.end:
                raise ValidationError("Window overlaps with {}".format(window))

    def validate_positive_timedelta(self):
        if self.start >= self.end:
            raise ValidationError("End is not after start")

    def clean(self):
        self.validate_positive_timedelta()
        self.validate_windows_dont_overlap()
        super().clean()


class Timer(models.Model):
    """Represent the time period in which a team can, for example, submit flags"""

    class Meta:
        unique_together = ('window', 'team',)

    id = models.AutoField(primary_key=True)

    window = models.ForeignKey(Window, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    start = models.DateTimeField(auto_now=True)
    end = models.DateTimeField(editable=False, blank=True)

    def __str__(self):
        return "<Timer #{} window=#{} team=#{} {} – {}>".format(
            self.id, self.window_id, self.team_id, print_time(self.start), print_time(self.end))

    def active(self):
        return self.start <= timezone.now() <= self.end

    def sync_end(self):
        self.end = timezone.now() + self.window.personal_timer_duration

    def clean(self):
        self.sync_end()


@receiver(post_save, sender=Window, dispatch_uid='ctf.window_post_save_update_timers')
def window_post_save_update_timers(sender, instance, **kwargs):
    """Make timers update their end timers per changes in their window"""
    for timer in instance.timer_set.all():
        timer.save()

# endregion


# region Permissions and Groups
#
# class GlobalPermissionManager(models.Manager):
#     def get_query_set(self):
#         return super(GlobalPermissionManager, self).filter(content_type__name='global_permission')
#
#
# class GlobalPermission(Permission):
#     """A global permission, not attached to a model"""
#
#     objects = GlobalPermissionManager()
#
#     class Meta:
#         proxy = True
#
#     def save(self, *args, **kwargs):
#         content_type, created = ContentType.objects.get_or_create(
#             model="global_permission", app_label=self._meta.app_label
#         )
#         self.content_type = content_type
#         super().save(*args, **kwargs)
#
# @receiver(post_save, sender=Competitor, dispatch_uid='ctf.competitor_post_save_add_to_group')
# def competitor_post_save_add_to_group(sender, instance, created, **kwargs):
#     if created:
#         competitorGroup = Group.objects.get(name=COMPETITOR_GROUP_NAME)
#         instance.user.groups.add(competitorGroup)
#
#
# @receiver(post_delete, sender=Competitor, dispatch_uid='ctf.competitor_post_delete_remove_from_group')
# def competitor_post_delete_remove_from_group(sender, instance, created, **kwargs):
#     if created:
#         competitorGroup = Group.objects.get(name=COMPETITOR_GROUP_NAME)
#         instance.user.groups.remove(competitorGroup)
#
# endregion


# region User Models (by substitution)
#
# class CompetitorManager(BaseUserManager):
#     def create_user(username, fullname, email, team, password=None):
#         pass
#
#     def create_superuser(self, username, fullname, email, team, password):
#         pass
#
# class Competitor(AbstractBaseUser):
#     username = models.CharField(max_length=40, unique=True)
#     fullname = models.CharField(max_length=100)
#     email = models.EmailField()
#     team = models.ForeignKey(Team, on_delete=models.CASCADE)
#
#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['fullname', 'email', 'team']
#
#     def get_short_name(self):
#         return self.username
#
#     def get_full_name(self):
#         return self.fullname
#
#     objects = CompetitorManager()
#
# endregion
