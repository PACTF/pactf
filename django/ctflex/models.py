"""Define models

Style Guidelines:
  - You SHOULD not use auto_now_add=True on DateTimeFields because it makes
    Django’s admin panel not show the field by default and absolutely not be
    able to edit the field.
"""

import re
import uuid

import markdown2
from django.contrib.postgres import fields as psql
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver as _receiver
from django.utils import timezone

from ctflex import settings
from ctflex.constants import APP_NAME, DEPS_PROBS_FIELD, DEPS_THRESHOLD_FIELD


# region Helpers


def print_time(time):
    """Format a datetime object to be human-readable"""
    return time.astimezone(tz=None).strftime('%m-%d@%H:%M:%S')


def unique_receiver(*args, **kwargs):
    """Decorate by wrapping `django.dispatch.receiver` to set `dispatch_uid` automatically

    Purpose:
        This decorator eliminates the need to set `dispatch_uid` for a Django
        receiver manually. You would want to set `dispatch_uid` to prevent a
        receiver from being run twice.

    Usage:
        Simply substitute this decorator for `django.dispatch.receiver`. If
        you define `dispatch_uid` yourself, this decorator will use that
        supplied value instead of the receiver function's name.

    Implementation Notes:
        - The default value for `dispatch_uid` (if you do not provide it
          yourself) is ‘ctflex’ composed with the receiver function’s name.
    """

    def decorator(function):
        default_dispatch_uid = '{}.{}'.format(APP_NAME, function.__name__)
        kwargs.setdefault('dispatch_uid', default_dispatch_uid)
        return _receiver(*args, **kwargs)(function)

    return decorator


def cleaned(cls):
    """Call individual cleaning methods and collect all of their ValidationErrors

    Purpose:
        This decorator allows you to write individual methods that do some
        validation or cleaning without having to worry about collecting all
        of their ValidationErrors together into a list and throwing one big
        ValidationError from the list (as is recommended to do per the
        Django documentation).

    Usage:
        Decorate your class with this decorator, and then define:
            a) the list of methods MODEL_CLEANERS (optional)
            b) the dictionary from field names to a list of methods FIELD_CLEANERS (optional)
        The method signatures must be just 'self'.

    Implementation Notes:
        - The superclass’s `clean_fields()` and `clean()` method will be called.
        - The `exclude` argument passed to `clean_fields()` will be used to
          exclude cleaning of fields based on the keys in FIELD_CLEANERS.

    Drawbacks:
        - This decorator will replace any defined clean_fields() and clean() methods
          (as opposed to decorating them).
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


# Validator for restricting a field to word characters
word_characters = validators.RegexValidator(
    regex=r'^\w*$',
    code='word_characters',
    message="Only alphanumeric characters and underscores are allowed."
)


def markdown_to_html(markdown):
    """Convert Markdown to HTML, quoting any existing HTML """
    return markdown2.markdown(markdown, extras=settings.MARKDOWN_EXTRAS, safe_mode='escape')


def link_static(text, *, static_prefix, text_prefix):
    """Parse {% ctflexstatic ... %} directives for linking to static files"""

    TAG = 'ctflexstatic'
    FILENAME_GROUP = 'filename'
    PATTERN = re.compile(
        r'''{{% \s* {} \s+ (['"]) (?P<{}> (?:(?!\1).)+ ) \1 \s* %}}'''
            .format(TAG, FILENAME_GROUP),
        re.VERBOSE,
    )
    REPLACEMENT = r'{}/{}/{{}}'.format(static_prefix, text_prefix)
    REPLACER = lambda match: static(REPLACEMENT.format(match.group(FILENAME_GROUP)))

    return PATTERN.sub(REPLACER, text)


# endregion


# region User Models

class Team(models.Model):
    """Represent a team"""

    ''' Structural Fields '''

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True,
                            verbose_name="Team Name")

    ''' Data Fields '''

    banned = models.BooleanField(default=False)
    passphrase = models.CharField(max_length=30,
                                  verbose_name="Passphrase")
    affiliation = models.CharField(max_length=60, blank=True,
                                   verbose_name="Affiliation")

    # FIXME: Change fixtures

    US_COUNTRY = 'U'
    OTHER_COUNTRY = 'O'
    COUNTRY_CHOICES = (
        (US_COUNTRY, "United States of America"),
        (OTHER_COUNTRY, "Other (ineligible for prizes)"),
    )
    country = models.CharField(max_length=1,
                               choices=COUNTRY_CHOICES, default=US_COUNTRY)

    SCHOOL_BACKGROUND = 'S'
    OTHER_BACKGROUND = 'O'
    BACKGROUND_CHOICES = (
        (SCHOOL_BACKGROUND, "Middle-school/High-school"),
        (OTHER_BACKGROUND, "Other (ineligible for prizes)"),
    )
    background = models.CharField(max_length=1,
                                  choices=BACKGROUND_CHOICES, default=SCHOOL_BACKGROUND)

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)

    ''' Properties '''

    def size(self):
        return self.competitor_set.count()

    def has_space(self):
        return self.size() < settings.MAX_TEAM_SIZE

    def timer(self, window):
        return self.timer_set.get(window=window)

    def has_timer(self, window):
        return self.timer_set.filter(window=window).exists()

    def has_active_timer(self, window=None):
        return self.has_timer(window) and self.timer(window).active()


@cleaned
class Competitor(models.Model):
    """Represent a competitor as a 'user profile' (in Django terminology)

    Some of Django's User model's fields are duplicated here, like first_name,
    last_name and email. We shun the email field for easier enforcement of
    uniqueness. We shun the other fields to simplify forms for creating a Competitor.
    """

    ''' Structural Fields '''

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.PROTECT)

    ''' Extra Data '''

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    # country = CountryField(default='US')
    # state = USStateField(blank=True, null=True)

    # MIDDLESCHOOL = 'M'
    # HIGHSCHOOL = 'H'
    # HOMESCHOOLED = 'E'
    # UNDERGRAD = 'U'
    # GRADUATE = 'G'
    # TEACHER = 'T'
    # PROFESSIONAL = 'P'
    # HOBBYIST = 'Y'
    # OTHER = 'O'
    # BACKGROUND_CHOICES = (
    #     (MIDDLESCHOOL, "Middle School Student"),
    #     (HIGHSCHOOL, "High School Student"),
    #     (HOMESCHOOLED, "Homeschooled"),
    #     (UNDERGRAD, "Undergraduate"),
    #     (GRADUATE, "Graduate Student"),
    #     (TEACHER, "Teacher"),
    #     (PROFESSIONAL, "Security Professional"),
    #     (HOBBYIST, "CTF Hobbyist"),
    #     (OTHER, "Other"),
    # )
    # background = models.CharField(max_length=1,
    #                               choices=BACKGROUND_CHOICES, default=HIGHSCHOOL)

    def __str__(self):
        return "<Competitor #{} {!r} team=#{}>".format(self.id, self.user.username, self.team.id)

    ''' Cleaning '''

    # def validate_state_is_given_for_us(self):
    #     if self.country == Country('US') and not self.state:
    #         raise ValidationError(
    #             "State is required if you are competing from the U.S.",
    #             code='state_is_given_for_us',
    #         )
    #
    # def sync_state_outside_us(self):
    #     if self.country != Country('US'):
    #         self.state = None

    def validate_team_has_space(self):
        try:
            team = self.team
        except Team.DoesNotExist:
            pass
        else:
            if not team.has_space():
                raise ValidationError("The team is already full.")

    FIELD_CLEANERS = {
        # 'state': [validate_state_is_given_for_us],
    }

    MODEL_CLEANERS = (
        # sync_state_outside_us,
        validate_team_has_space,
    )


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
        """Return the 'current' window

        The 'current' window is defined as the window that fits the first
        of the following criteria:
        - The window is currently ongoing.
        - The window is the next to begin.
        - The window was the last to have ended.
        """
        now = timezone.now()
        try:
            return self.get(start__lte=now, end__gte=now)
        except Window.DoesNotExist:
            return (self.filter(start__gte=now).order_by('start').first()
                    or self.order_by('-start').first())


@cleaned
class Window(models.Model):
    """Represent a Window"""

    objects = WindowManager()

    id = models.AutoField(primary_key=True)
    codename = models.CharField(max_length=30, unique=True,
                                validators=[word_characters],
                                help_text="Human-readable identifier")
    verbose_name = models.CharField(max_length=30, unique=True, blank=False,
                                    help_text="User-facing title of window")

    start = models.DateTimeField()
    end = models.DateTimeField()
    personal_timer_duration = models.DurationField()

    def __str__(self):
        return "<Window #{} {!r} {} – {}>".format(self.id, self.codename, print_time(self.start), print_time(self.end))

    ''' Properties '''

    def started(self):
        return self.start <= timezone.now()

    def ended(self):
        return self.end < timezone.now()

    def ongoing(self):
        return self.started() and not self.ended()

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

    def validate_window_is_not_named_overall(self):
        if self.codename == settings.OVERALL_WINDOW_CODENAME:
            raise ValidationError("The window codename cannot be {!r}".format(settings.OVERALL_WINDOW_CODENAME))

    def sync_timers(self):
        """Make timers update their end times per changes in the personal window duration

        Purpose:
          - Make timers update their end based on the window's personal_timer_duration;
          - Raise a ValidationError if the timers would be outside the window if modified;
        """
        for timer in self.timer_set.all():
            timer.save()

    MODEL_CLEANERS = (
        validate_windows_dont_overlap,
        validate_timedelta_is_positive,
        validate_window_is_not_named_overall,
        sync_timers,
    )


@cleaned
class Timer(models.Model):
    """Represent a Timer"""

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
        if not self.start:
            self.start = timezone.now()

    def sync_end(self):
        self.end = min(self.start + self.window.personal_timer_duration, self.window.end)

    def validate_timer_is_within_window(self):
        if self.start < self.window.start or self.end > self.window.end:
            raise ValidationError("Timer does not lie within window", code='timer_is_within_window')

    # (The order  matters here.)
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

    class Meta:
        verbose_name = "Problem"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    window = models.ForeignKey(Window)

    points = models.IntegerField(validators=[validators.MinValueValidator(1), ])

    description = models.TextField(default='', blank=True)
    description_html = models.TextField(editable=False, default='', blank=True)
    hint = models.TextField(default='', blank=True)
    hint_html = models.TextField(editable=False, default='', blank=True)

    grader = models.FilePathField(
        max_length=200, path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$',
        help_text="Basename of the problem's grading script in PROBLEMS_DIR",
    )
    generator = models.FilePathField(
        max_length=200, path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$',
        blank=True, null=True,
        help_text="Basename of the problem's generator script in PROBLEMS_DIR",
    )

    # Dictionary for problem dependencies in format specified in README
    deps = psql.JSONField(blank=True, null=True)

    def __str__(self):
        return "<Problem #{} {!r}>".format(self.id, self.name)

    ''' Helpers '''

    def process_html(self, text):
        return link_static(
            markdown_to_html(text),
            static_prefix=settings.PROBLEMS_STATIC_URL,
            text_prefix=self.id,
        )

    ''' Cleaning '''

    def validate_deps(self):
        if self.deps is not None:

            if not set(self.deps.keys()).issubset({DEPS_THRESHOLD_FIELD, DEPS_PROBS_FIELD}):
                raise ValidationError(
                    "The dependencies field can only contain the keys {} and {}"
                        .format(DEPS_PROBS_FIELD, DEPS_THRESHOLD_FIELD),
                    code='deps',
                )

            if DEPS_THRESHOLD_FIELD in self.deps:
                score = self.deps[DEPS_THRESHOLD_FIELD]
                if type(score) != int or score <= 0:
                    raise ValidationError(
                        "The field {} must be a positive integer".format(DEPS_THRESHOLD_FIELD),
                        code='deps',
                    )

            if DEPS_PROBS_FIELD in self.deps:
                probs = self.deps[DEPS_PROBS_FIELD]
                if type(probs) != list:
                    raise ValidationError(
                        "The field {} must be an iterable".format(DEPS_PROBS_FIELD),
                        code='deps',
                    )

    def sync_empty_deps_fields(self):
        if self.deps is not None:

            # A threshold of one means "at least one of the problems"
            if DEPS_THRESHOLD_FIELD not in self.deps:
                self.deps[DEPS_THRESHOLD_FIELD] = 1

            # An empty tuple is interpreted as including all problems (per the spec)
            if DEPS_PROBS_FIELD not in self.deps:
                self.deps[DEPS_PROBS_FIELD] = ()

    def validate_desc_and_hint_exist_or_not(self):
        if self.generator and (self.description or self.hint):
            raise ValidationError(
                "Description and hints should not be statically provided for dynamic problems",
                code='desc_and_hint_exist_or_not'
            )
        elif not self.generator and not self.description:
            raise ValidationError(
                "Description must be provided statically for simple problems",
                code='desc_and_hint_exist_or_not'
            )

    def sync_html(self):
        if not self.generator:
            self.description_html = self.process_html(self.description)
            self.hint_html = self.process_html(self.hint)

    FIELD_CLEANERS = {
        # (The order matters here.)
        'deps': (
            sync_empty_deps_fields,
            validate_deps,
        ),
    }

    # (The order matters here.)
    MODEL_CLEANERS = (
        validate_desc_and_hint_exist_or_not,
        sync_html,
    )


@cleaned
class Solve(models.Model):
    """Record currently applicable solves of a problem

    This model is also used to compute the score of a team.
    """

    class Meta:
        unique_together = ('problem', 'competitor')

    problem = models.ForeignKey(CtfProblem)
    competitor = models.ForeignKey(Competitor)

    date = models.DateTimeField()
    flag = models.CharField(max_length=100, blank=False)

    def __str__(self):
        return "<Solve prob={} team={} date={}>".format(self.problem, self.competitor.team, self.date)

    ''' Cleaning '''

    def sync_date(self):
        if not self.date:
            self.date = timezone.now()

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

    FIELD_CLEANERS = {
        'date': (
            sync_date,
        )
    }

    MODEL_CLEANERS = (
        validate_teams_are_unique,
        validate_time_inside_window,
        validate_time_not_in_future,
    )


@cleaned
class Submission(models.Model):
    """Log a flag submission attempt

    This model serves only as a log and instances may be deleted without
    consequence. The one other purpose this model serves is telling a competitor
    they already tried a particular flag.

    There is a `p_id` field in addition to the `problem` foreign key. This enables
    deleting problems without needing to delete the associated Submissions. This
    doubling of fields is not done with the competitor field as
    - IDs are less useful for deleted competitors
    - competitor objects are less likely to be deleted since typically one would
      simply set is_active flag of a user to False instead of deleting the objects.
    """

    id = models.AutoField(primary_key=True)
    p_id = models.UUIDField()
    problem = models.ForeignKey(CtfProblem, on_delete=models.SET_NULL,
                                null=True, blank=True, editable=False)
    competitor = models.ForeignKey(Competitor, on_delete=models.SET_NULL, null=True)

    date = models.DateTimeField(auto_now_add=True)
    flag = models.CharField(max_length=100, blank=True)
    correct = models.NullBooleanField()

    def __str__(self):
        return "<Submission @{} problem={} competitor={}>".format(self.date, self.problem, self.competitor)

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

# region Miscellaneous


@unique_receiver(pre_save)
def pre_save_validate(sender, instance, *args, **kwargs):
    """Full clean an object before saving it

    Purpose:
        While forms typically full clean an object before saving it, other
        code might not always do this. To prevent invalid objects from being
        saved, this receiver makes saving an object full clean it first.

    Usage:
        This receiver has already been registered. Nothing more needs to
        be done.

    Implementation Notes:
        - This receiver ignores non-CTFlex models since otherwise errors happen.

    Drawbacks:
        - This receiver means that full_clean is sometimes redundantly called
          twice for an object.

    Limitations:
        - Calling update() on a query does not trigger save() and thus still
          doesn't trigger full_clean().

    Author: Yatharth
    """
    if sender._meta.app_label == APP_NAME:
        instance.full_clean()


# class State(models.Model):
#     """Track global settings in the database"""
#
#     def save(self, *args, **kwargs):
#         self.id = 1
#         super().save(*args, **kwargs)


@cleaned
class Announcement(models.Model):
    """Represent an announcement for a window (and maybe some problems)"""

    ''' Structural Fields '''

    id = models.AutoField(primary_key=True)
    window = models.ForeignKey(Window, on_delete=models.CASCADE)
    competitors = models.ManyToManyField(Competitor, related_name='unread_announcements',
                                         blank=True)
    problems = models.ManyToManyField(CtfProblem, blank=True)

    ''' Data Fields '''

    date = models.DateTimeField()

    title = models.CharField(max_length=100)
    title_html = models.CharField(max_length=100, editable=False, blank=True)
    body = models.TextField(blank=False)
    body_html = models.TextField(editable=False, default='', blank=True)

    def __str__(self):
        return "<Announcement #{} window={!r} {}>".format(self.id, self.window, print_time(self.date))

    ''' Cleaning '''

    def sync_date(self):
        if not self.date:
            self.date = timezone.now()

    # def sync_title_is_single_line(self):
    #     self.title = self.title.replace('\n', ' ')

    def sync_html(self):
        self.body_html = markdown_to_html(self.body)
        self.title_html = markdown_to_html(self.title)

    def validate_windows(self):
        """Validate that the announcement window and any problem windows are the same

        Usage:
            1. Begin a transaction with `with transaction.atomic()`
            2. Make your many-to-many field changes to `problems`
            3. Call this method

            This method may raise a ValidationError, which you may catch
            outside (NOT inside) the transaction manager.

        Limitations:
            - This validation cannot be performed automatically, so you must
              code it in yourself.
        """
        if self.problems:
            problem_windows = set(obj['window'] for obj in self.problems.values('window'))
            if not problem_windows.issubset({self.window.id}):
                raise ValidationError("Associated problems’ windows must match the announcement’s window",
                                      code='window')

    FIELD_CLEANERS = {
        'date': (
            sync_date,
        ),
    }

    # (Order doesn’t matter.)
    MODEL_CLEANERS = (
        sync_html,
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
