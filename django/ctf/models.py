from os.path import join
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager

from django.db import models
from django.conf import settings
from django.auth.models import User
from django.contrib.postgres import fields as psqlmodels

import importlib.machinery
import markdown2

from ctf.auth import *

class CtfProblem(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=20)

    points = models.IntegerField()
    # TODO(Cam): Eliminate _html fields and just convert in-place in the save() method
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
        # TODO(Yatharth): Have real team id forwarded
        if not flag:
            return False, "Empty flag"

        grader_path = join(settings.PROBLEMS_DIR, self.grader)
        grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()
        correct, message = grader.grade(1, flag)
        return correct, message

    def save(self, **kwargs):
        EXTRAS = ('fenced-code-blocks', 'smarty-pants', 'spoiler')

        self.description_html = markdown2.markdown(
            self.description, extras=EXTRAS, safe_mode=True
        )
        self.hint_html = markdown2.markdown(
            self.hint, extras=EXTRAS, safe_mode=True
        )

        self.full_clean()
        super().save(**kwargs)


class Team(models.Model):
    """
    TODO(Yatharth): Make this work relationally
    The format of the submissions dict is {p_id:solves}
    flags is a list of submitted flags.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True)
    score = models.IntegerField(default=0)
    submissions = psqlmodels.JSONField(default={})

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)


# TODO(Yatharth): Grandfather
# TODO(Yatharth): Make email unique and required, and change other Django User's fields (or shun them)
class Competitor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)

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
