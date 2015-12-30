from os.path import join

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

import importlib.machinery
import markdown2


# region User Models (by wrapping)

class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)


class Competitor(models.Model):
    """Represents a competitor 'profile'

    Django's User class's fields are shunned. The only ones that are used are:

        username, password, is_active, is_staff, date_joined

    """

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    # Shunned fields
    first_name = models.CharField("First name", max_length=30, blank=True)
    last_name = models.CharField("Last name", max_length=30, blank=True)
    email = models.EmailField("Email", unique=True)

    # TODO(Yatharth): Is this useful? It can be set but not filtered against.
    @property
    def username(self):
        return self.user.username

# endregion


# region Contest Models

class CtfProblem(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=20)

    points = models.IntegerField()
    description = models.TextField()
    description_html = models.TextField(editable=False)
    hint = models.TextField(default='')
    hint_html = models.TextField(editable=False, blank=True, null=True)

    grader = models.FilePathField(
        help_text="Basename of the grading script from PROBLEM_DIR",
        path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$'
    )

    def __str__(self):
        return "<Problem #{} {!r}>".format(self.id, self.name)

    def grade(self, flag):
        # FIXME(Yatharth): Have real team id forwarded
        if not flag:
            return False, "Empty flag"

        grader_path = join(settings.PROBLEMS_DIR, self.grader)
        grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()
        correct, message = grader.grade(1, flag)
        return correct, message

    def save(self, **kwargs):
        EXTRAS = ('fenced-code-blocks', 'smarty-pants', 'spoiler')

        # markdown's safe_mode is deprecated
        self.description_html = markdown2.markdown(self.description, extras=EXTRAS, safe_mode='escape')
        self.hint_html = markdown2.markdown(self.hint, extras=EXTRAS, safe_mode='escape')
        self.full_clean()
        super().save(**kwargs)

# FIXME(Yatharth): Review Submission model
class Submission(models.Model):
    p_id = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
    # FIXME: Rename to competitor
    user = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, editable=False, blank=True)
    flag = models.CharField(max_length=80)
    correct = models.BooleanField()

    def save(self, **kwargs):
        self.team = self.user.team
        super().save(**kwargs)

# endregion


# region User Models (by substitution)

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

# endregion
