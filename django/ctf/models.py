from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

import importlib.util
import markdown2


# TODO(Cam): make a JSONField or something similar to store the threshold dict
class CtfProblem(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=20)

    points = models.IntegerField()

    description = models.TextField()
    description_html = models.TextField(editable=False)
    hint = models.TextField(default='')
    hint_html = models.TextField(editable=False, blank=True, null=True)

    grader = models.FilePathField(
        help_text='Path to the grading script',
        path=settings.PROBLEMS_DIR, recursive=True, match=r'.*\.py'
    )


    def grade(self, flag):
        spec = importlib.util.spec_from_file_location('grader.py', self.grader)
        grader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grader)
        return grader.grade(flag)

    def save(self, **kwargs):
        EXTRAS = ('fenced-code-blocks', 'smarty-pants', 'spoiler')

        self.description_html = markdown2.markdown(
            self.description, extras=EXTRAS
        )
        self.hint_html = markdown2.markdown(
            self.hint, extras=EXTRAS
        )

        self.full_clean()
        super().save(**kwargs)


class Team(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
