from os.path import join

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

import importlib.machinery
import markdown2

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

        # markdown's safe_mode is deprecated
        self.description_html = markdown2.markdown(self.description, extras=EXTRAS, safe_mode='escape')
        self.hint_html = markdown2.markdown(self.hint, extras=EXTRAS, safe_mode='escape')
        self.full_clean()
        super().save(**kwargs)


class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    score = models.IntegerField(default=0)

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)


class Competitor(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)


class Submission(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    p_id = models.IntegerField()
    user = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, editable=False, blank=True)
    flag = models.CharField(max_length=80)
    correct = models.BooleanField()

    def save(self, **kwargs):
        self.team = self.user.team
        super().save(**kwargs)
