import re
import uuid
import random, string
from os.path import join
import importlib.machinery

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.postgres import fields as psql
import markdown2

from ctflex.constants import APP_NAME


# TODO(Yatharth): Write helper so error of clean returns all validationerrors


# region Helpers and General

print_time = lambda time: time.astimezone(tz=None).strftime('%m-%d@%H:%M:%S')

def unique_receiver(*args, **kwargs):
    """Wrap Django's `receiver` to set dispatch_uid automatically based on the function's name"""

    def decorator(function):
        default_dispatch_uid = '{}.{}'.format(APP_NAME, function.__name__)
        kwargs.setdefault('dispatch_uid', default_dispatch_uid)
        return receiver(*args, **kwargs)(function)

    return decorator


@unique_receiver(pre_save)
def pre_save_validate(sender, instance, *args, **kwargs):
    instance.full_clean()

# class Config(models.Model):
#     default_category = models.ForeignKey(Category)
#
#     def save(self, *args, **kwargs):
#         self.id = 1
#         super().save(*args, **kwargs)


# endregion


# region User Models (by wrapping)

# def gen_key(chars=string.ascii_uppercase + string.digits):
#     return ''.join(random.choice(chars) for _ in range(20))

class Team(models.Model):
    """Represent essence of a team"""


    # Essential data
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True)

    # key = models.CharField(max_length=30, default=gen_key)

    # Extra data
    school = models.CharField(max_length=40, blank=True, default='None')

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)

    # XXX(Yatharth): Put into queries or sth
    def score(self, window):
        score = 0
        for competitor in self.competitor_set.all():
            for solve in competitor.solve_set.filter(problem__window=window):
                score += solve.problem.points
        return score

    # XXX(Yatharth): Remove default params
    def timer(self, window=None):
        if window is None:
            window = Window.current()
        return self.timer_set.get(window=window)

    def has_timer(self, window=None):
        try:
            self.timer(window=window)
        except Timer.DoesNotExist:
            return False
        else:
            return True

    def has_active_timer(self, window=None):
        return self.has_timer(window) and self.timer(window).active()

    def can_view_problems(self, window=None):
        return self.has_timer(window=window) and self.timer(window=window).start <= timezone.now()

    def start_timer(self, window):
        assert not self.has_timer()

        timer = Timer(window=window, team=self)
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


# region Timer Models


class Window(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, blank=False)

    start = models.DateTimeField()
    end = models.DateTimeField()

    personal_timer_duration = models.DurationField()

    def __str__(self):
        return "<Window #{} {} – {}>".format(self.id, print_time(self.start), print_time(self.end))

    """ Properties """

    def started(self):
        return self.start <= timezone.now()

    def ended(self):
        return self.end < timezone.now()

    """ Class methods """

    @staticmethod
    def current():
        now = timezone.now()
        try:
            return Window.objects.get(start__lte=now, end__gte=now)
        except Window.DoesNotExist:
            return Window.objects.filter(start__gte=now).order_by('start').first() or \
                     Window.objects.order_by('-start').first()

    """ Validation """

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
        super().clean()
        self.sync_end()


@unique_receiver(post_save, sender=Window)
def window_post_save_update_timers(sender, instance, **kwargs):
    """Make timers update their end timers per changes in their window"""
    for timer in instance.timer_set.all():
        timer.save()

# endregion


# region Problem Models

# XXX(Yatharth): Move stuff out
class CtfProblem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    window = models.ForeignKey(Window)

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
        # XXX(Yatharth): Handle FileNotFound
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
        PATTERN = re.compile(r'''{% \s* ctflexstatic \s+ (['"]) (?P<basename> (?:(?!\1).)+ ) \1 \s* (%})''', re.VERBOSE)
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


class Solve(models.Model):

    class Meta:
        unique_together = ('problem', 'competitor')

    problem = models.ForeignKey(CtfProblem)
    competitor = models.ForeignKey(Competitor)

    date = models.DateTimeField(auto_now=True)
    flag = models.CharField(max_length=100, blank=False)


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


# region Permissions and Groups (old)
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
# @unique_receiver(post_save, sender=Competitor)
# def competitor_post_save_add_to_group(sender, instance, created, **kwargs):
#     if created:
#         competitorGroup = Group.objects.get(name=COMPETITOR_GROUP_NAME)
#         instance.user.groups.add(competitorGroup)
#
#
# @unique_receiver(post_delete, sender=Competitor)
# def competitor_post_delete_remove_from_group(sender, instance, created, **kwargs):
#     if created:
#         competitorGroup = Group.objects.get(name=COMPETITOR_GROUP_NAME)
#         instance.user.groups.remove(competitorGroup)
#
# endregion (o (old)


# region User Models (by substitution) (old)
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
