"""Define CTFlex's models"""

import re
import uuid

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver as _receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.postgres import fields as psql
from django_countries.fields import CountryField, Country

import markdown2
from localflavor.us.models import USStateField

from ctflex.constants import APP_NAME


# region Helpers and General

def print_time(time):
    """Format a datetime object to be human-readable"""
    return time.astimezone(tz=None).strftime('%m-%d@%H:%M:%S')


def unique_receiver(*args, **kwargs):
    """Wrap django.dispatch.receiver to set dispatch_uid automatically based on the receiver's name

    Purpose: This decorator eliminates the need to set dispatch_uid automatically. It is recommended to set dispatch_uid to prevent a receiver from being run twice.

    Usage: This decorator should be always used instead of django.dispatch.receiver.
    """

    def decorator(function):
        default_dispatch_uid = '{}.{}'.format(APP_NAME, function.__name__)
        kwargs.setdefault('dispatch_uid', default_dispatch_uid)
        return _receiver(*args, **kwargs)(function)

    return decorator


@unique_receiver(pre_save)
def pre_save_validate(sender, instance, *args, **kwargs):
    """Full clean an object before saving it

    Purpose: This receiver ensures models are not accidentally manually modified and saved without being validated.

    Drawbacks:
    - This receiver means that full_clean is sometimes called twice for an object.
    - Calling update() on a query does not trigger save() and thus still doesn't trigger full_clean().
    """
    instance.full_clean()


def cleaned(cls):
    """Call individual cleaning methods and collect all of their ValidationErrors

    Usage: To use this decorator, you may define a) the list of methods MODEL_CLEANERS and/or b) the dictionary from field names to a list of methods FIELD_CLEANERS. The method signatures must be just 'self'.

    Purpose: This decorator calls methods in FIELD_CLEANERS or MODEL_CLEANERS along with the super class's clean_fields() or clean() method. It collects any and all of the ValidationErrors and raises them as one big ValidationError. It excludes fields in clean_fields() based on the keys in FIELD_CLEANERS.

    Drawbacks: This decorator will replace any defined clean_fields() and clean() methods instead of decorate them.
    """

    def clean(self):

        errors = []
        for validator in getattr(self, 'MODEL_CLEANERS', []):
            try:
                validator(self)
            except ValidationError as error:
                errors.append(error)

        try:
            super(cls, self).clean()
        except ValidationError as error:
            errors.append(error)

        if errors:
            raise ValidationError(errors)

    def clean_fields(self, exclude=None):

        if exclude is None:
            exclude = ()

        errors = []
        for field_name, validators in getattr(self, 'FIELD_CLEANERS', {}).items():
            if field_name not in exclude:
                for validator in validators:

                    try:
                        validator(self)
                    except ValidationError as error:
                        errors.append(error)

        try:
            super(cls, self).clean_fields(exclude=exclude)
        except ValidationError as error:
            errors.append(error)

        if errors:
            raise ValidationError(errors)

    cls.clean_fields = clean_fields
    cls.clean = clean

    return cls


# class Config(models.Model):
#     default_category = models.ForeignKey(Category)
#
#     def save(self, *args, **kwargs):
#         self.id = 1
#         super().save(*args, **kwargs)


# endregion


# region User Models

class Team(models.Model):
    """Represent a team"""

    ''' Structural Fields '''

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=30)
    banned = models.BooleanField(default=False)

    ''' Extra Data '''

    affiliation = models.CharField(max_length=60, blank=True)

    # advisor_name = models.CharField(max_length=40, blank=True)
    # advisor_email = models.EmailField(blank=True)

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)

    ''' Properties '''

    def timer(self, window):
        return self.timer_set.get(window=window)

    def has_timer(self, window):
        return self.timer_set.filter(window=window).exists()

    def has_active_timer(self, window=None):
        return self.has_timer(window) and self.timer(window).active()


@cleaned
class Competitor(models.Model):
    """Represent a competitor as a 'user profile' (in Django terminology)

    Some of Django's User model's fields are shunned, like first_name, last_name and email. We shun the email field for easier enforcement of uniqueness. We shun Django's User model's fields in general to reduce our dependency on it for data fields. This way, the only data fields stored primarily in in Django's User model are username and password. These are few enough fields to be able to manually hack on to a ModelForm for Competitor instead of needing to combine ModelForm each for Competitor and User, for example.
    """

    ''' Structural Fields '''

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    unread_announcements = models.ManyToManyField(Announcement)

    ''' Extra Data '''

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    country = CountryField(default='US')
    state = USStateField(blank=True, null=True)

    MIDDLESCHOOL = 'M'
    HIGHSCHOOL = 'H'
    HOMESCHOOLED = 'E'
    UNDERGRAD = 'U'
    GRADUATE = 'G'
    TEACHER = 'T'
    PROFESSIONAL = 'P'
    HOBBYIST = 'Y'
    OTHER = 'O'
    BACKGROUND_CHOICES = (
        (MIDDLESCHOOL, "Middle School Student"),
        (HIGHSCHOOL, "High School Student"),
        (HOMESCHOOLED, "Homeschooled"),
        (UNDERGRAD, "Undergraduate"),
        (GRADUATE, "Graduate Student"),
        (TEACHER, "Teacher"),
        (PROFESSIONAL, "Security Professional"),
        (HOBBYIST, "CTF Hobbyist"),
        (OTHER, "Other"),
    )
    background = models.CharField(max_length=1, choices=BACKGROUND_CHOICES, default=HIGHSCHOOL)

    def __str__(self):
        return "<Competitor #{} {!r}>".format(self.id, self.user.username)

    ''' Cleaning '''

    def validate_state_is_given_for_us(self):
        if self.country == Country('US') and not self.state:
            raise ValidationError("State is required if you are competing from the U.S.", code='state_is_given_for_us')

    def sync_state_outside_us(self):
        if self.country != Country('US'):
            self.state = None

    FIELD_CLEANERS = {
        'state': [validate_state_is_given_for_us],
    }

    MODEL_CLEANERS = (
        sync_state_outside_us,
    )

@cleaned
class Announcement(models.Model):
    a_id = models.IntegerField
    title = models.CharField(max_length=80, blank=False)
    body = models.TextField(blank=False)
    posted = models.DateTimeField(auto_now_add=True)
    problems = models.ManyToManyField(CtfProblem)

    def save(self):
        EXTRAS = ('fenced-code-blocks', 'smarty-pants', 'spoiler')
        self.body = markdown2.markdown(self.body, extras=EXTRAS, safe_mode='escape')
        self.title = markdown2.markdown(self.title.replace('\n', ' '), safe_mode='escape')


@unique_receiver(post_save, sender=Competitor)
def competitor_post_save_sync_to_user(sender, instance, **kwargs):
    """Update User fields based on Competitor fields"""

    instance.user.first_name = instance.first_name
    instance.user.last_name = instance.last_name
    instance.user.email = instance.email

    instance.user.save()

# endregion


# region Window Models

class WindowManager(models.Manager):
    def current(self):
        """Return 'current' window

        The 'current' window is defined as the window that fits the highest of the following criteria:
        - The window is currently going on.
        - The window is the next to begin.
        - The window was the last to have ended.
        """
        now = timezone.now()
        try:
            return self.get(start__lte=now, end__gte=now)
        except Window.DoesNotExist:
            return self.filter(start__gte=now).order_by('start').first() or \
                   self.order_by('-start').first()

    def other(self, window):
        return self.exclude(pk=window.id)


@cleaned
class Window(models.Model):
    """Represent a Contest Window"""

    objects = WindowManager()

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=30, unique=True,
                            help_text="Non-user-facing human-readable identifier for window")
    verbose_name = models.CharField(max_length=30, unique=True, blank=False,
                                    help_text="User-facing title of window")

    start = models.DateTimeField()
    end = models.DateTimeField()

    personal_timer_duration = models.DurationField()

    def __str__(self):
        return "<Window #{} {!r} {} – {}>".format(self.id, self.code, print_time(self.start), print_time(self.end))

    ''' Properties '''

    def started(self):
        return self.start <= timezone.now()

    def ended(self):
        return self.end < timezone.now()

    ''' Cleaning '''

    def validate_windows_dont_overlap(self):
        for other_window in Window.objects.exclude(id=self.id):
            if other_window.start <= self.end and self.start <= other_window.end:
                raise ValidationError(
                    "The window overlaps with another window: %(other_window)s",
                    code='windows_dont_overlap',
                    params={'other_window': other_window}
                )

    def validate_timedelta_is_positive(self):
        if self.start >= self.end:
            raise ValidationError("The end is not after the start", code='timedelta_is_positive')

    def sync_timers(self):
        """Make timers update their end times per changes in the personal window duration

        This method achieves two goals:
        - Make timers update their end based on the window's personal_timer_duration;
        - Raise ValidationErrors if the timers would be outside the window if modified;
        """
        for timer in self.timer_set.all():
            timer.save()

    MODEL_CLEANERS = (
        validate_windows_dont_overlap,
        validate_timedelta_is_positive,
        sync_timers,
    )


@cleaned
class Timer(models.Model):
    """Represent a Personal Timer"""

    class Meta:
        unique_together = ('window', 'team',)

    id = models.AutoField(primary_key=True)

    window = models.ForeignKey(Window, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    start = models.DateTimeField(blank=True)
    end = models.DateTimeField(blank=True)

    def __str__(self):
        return "<Timer #{} window=#{} team=#{} {} – {}>".format(
            self.id, self.window_id, self.team_id, print_time(self.start), print_time(self.end))

    ''' Properties '''

    def active(self):
        return self.start <= timezone.now() <= self.end

    ''' Cleaning '''

    def sync_start(self):
        """Set start to now if not already defined

        We do not simply set auto_now=True on the start field because then we can't edit the field in th Django admin panel.
        """
        if not self.start:
            self.start = timezone.now()

    def sync_end(self):
        self.end = timezone.now() + self.window.personal_timer_duration

    def validate_timer_is_within_window(self):
        if self.start < self.window.start or self.end > self.window.end:
            raise ValidationError("Timer does not lie within window", code='timer_is_within_window')

    # (The order of the following methods matters.)
    MODEL_CLEANERS = (
        sync_start,
        sync_end,
        validate_timer_is_within_window,
    )


# endregion


# region Problem Models

@cleaned
class CtfProblem(models.Model):
    """Represent a CTF Problem"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60)
    window = models.ForeignKey(Window)

    points = models.IntegerField()
    description = models.TextField(default='', blank=True)
    description_html = models.TextField(editable=False, default='', blank=True)
    hint = models.TextField(default='', blank=True)
    hint_html = models.TextField(editable=False, default='', blank=True)

    grader = models.FilePathField(
        help_text="Basename of the problem's grading script in PROBLEMS_DIR",
        max_length=200, path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$'
    )
    dynamic = models.FilePathField(
        help_text="Basename of the problem's generator script in PROBLEMS_DIR",
        max_length=200, path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$',
        blank=True, null=True,
    )

    # Dictionary for problem dependencies in format specified in README
    # (`dict` is used instead of `{}` because all objects would share dict otherwise.)
    deps = psql.JSONField(default=dict, blank=True)

    def __str__(self):
        return "<Problem #{} {!r}>".format(self.id, self.name)

    ''' Helpers '''

    @staticmethod
    def markdown_to_html(markdown):
        """Convert Markdown to HTML, quoting any existing HTML """
        EXTRAS = ('fenced-code-blocks', 'smarty-pants', 'spoiler')
        return markdown2.markdown(markdown, extras=EXTRAS, safe_mode='escape')

    @staticmethod
    def link_static(old_text, id):
        """Replace {% ctflexstatic %} directives with the appropriate static file link"""

        PATTERN = re.compile(r'''{% \s* ctflexstatic \s+ (['"]) (?P<basename> (?:(?!\1).)+ ) \1 \s* (%})''', re.VERBOSE)
        REPLACEMENT = r'{}/{}/{{}}'.format(settings.PROBLEMS_STATIC_URL, id)
        REPLACER = lambda match: static(REPLACEMENT.format(match.group('basename')))

        return PATTERN.sub(REPLACER, old_text)

    def process_html(self, html):
        return self.markdown_to_html(self.link_static(html, self.id))

    ''' Cleaning '''

    def validate_deps(self):
        if self.deps:
            if list(filter(lambda x:x not in ('score', 'probs'), self.deps.keys())):
                raise ValidationError(
                    "The field deps can only contain the keys score and probs",
                    code='deps',
                )

            if 'score' in self.deps:
                score = self.deps['score']
                if type(score) != int or score <= 0:
                    raise ValidationError(
                        "The field score must be a positive integer",
                        code='deps',
                    )

            if 'probs' in self.deps:
                probs = self.deps['probs']
                if type(probs) != list:
                    raise ValidationError(
                        "The field probs must be an array",
                        code='deps',
                    )

    def validate_desc_and_hint_exist_or_not(self):
        if self.dynamic and (self.description or self.hint):
            raise ValidationError(
                "Description and hints should not be statically provided for dynamic problems",
                code='desc_and_hint_exist_or_not'
            )
        elif not self.dynamic and not self.description:
            raise ValidationError(
                "Description must be provided statically for simple problems",
                code='desc_and_hint_exist_or_not'
            )

    def sync_html(self):
        if not self.dynamic:
            self.description_html = self.process_html(self.description)
            self.hint_html = self.process_html(self.hint)

    FIELD_CLEANERS = {
        'deps': (validate_deps,),
    }

    # (The order matters here.)
    MODEL_CLEANERS = (
        validate_desc_and_hint_exist_or_not,
        sync_html,
    )


@cleaned
class Solve(models.Model):
    """Record currently applicable solves of a problem

    This model is used to compute the score, among other things.
    """

    class Meta:
        unique_together = ('problem', 'competitor')

    problem = models.ForeignKey(CtfProblem)
    competitor = models.ForeignKey(Competitor)

    date = models.DateTimeField(auto_now=True)
    flag = models.CharField(max_length=100, blank=False)

    def __str__(self):
        return "<Solve prob={} team={}>".format(self.problem, self.competitor.team)

    ''' Cleaning '''

    def validate_teams_are_unique(self):
        if Solve.objects.filter(problem=self.problem, competitor__team=self.competitor.team).exclude(
                pk=self.id).exists():
            raise ValidationError(
                "A team can solve a problem only once",
                code='teams_are_unique',
            )

    def validate_time_inside_window(self):
        date = self.date
        window = self.problem.window
        team = self.competitor.team

        if date:
            if date < window.start or (team.has_timer(window) and date < team.timer(window).start):
                raise ValidationError("Solve happened before window or timer began", code='time_inside_window')

    def validate_time_not_in_future(self):
        if self.date and self.date > timezone.now():
            raise ValidationError("Solve occurs in future", code='time_not_in_future')

    MODEL_CLEANERS = (
        validate_teams_are_unique,
        validate_time_inside_window,
        validate_time_not_in_future,
    )


@cleaned
class Submission(models.Model):
    """Log a flag submission attempt

    This model serves only as a log and is not part of the truth (as defined in the Design Doc). The one other purpose t is used for is telling a competitor they already tried a particular flag.

    There is a `p_id` field in addition to the `problem` foreign key. This enables deleting problems while not deleting Submissions. This doubling of fields is not done with the competitor field as 1) IDs are less useful for deleted competitors and 2) competitor objects are less likely to be deleter since users and usually simply have the is_active flag set to False instead of having themselves deleted.
    """

    id = models.AutoField(primary_key=True)
    p_id = models.UUIDField()
    problem = models.ForeignKey(CtfProblem, on_delete=models.SET_NULL, null=True, blank=True, editable=False)
    competitor = models.ForeignKey(Competitor, on_delete=models.SET_NULL, null=True)

    time = models.DateTimeField(auto_now_add=True)
    flag = models.CharField(max_length=100, blank=True)
    correct = models.NullBooleanField()

    def __str__(self):
        return "<Submission @{} problem={} competitor={}>".format(self.time, self.problem, self.competitor)

    ''' Cleaning '''

    def sync_problem(self):
        try:
            self.problem = CtfProblem.objects.get(pk=self.p_id)
        except CtfProblem.DoesNotExist:
            pass

    MODEL_CLEANERS = (
        sync_problem,
    )

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
# endregion


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
