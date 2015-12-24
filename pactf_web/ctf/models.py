from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

import importlib.util
import markdown2


# TODO - make a JSONField or something similar to store the threshold dict
class CTFProblem(models.Model):
    id = models.AutoField(primary_key=True)
    points = models.IntegerField()
    name = models.CharField(unique=True, max_length=20)
    desc = models.TextField()
    desc_html = models.TextField(editable=False, blank=True, null=True)
    hint = models.TextField(default='')
    hint_html = models.TextField(editable=False, blank=True, null=True)
    grader = models.FilePathField(
        help_text='Path to the grading script',
        path=settings.PROBLEMS_DIR, recursive=True, match='*.py'
    )

    def grade(self, flag):
        # spec = importlib.util.spec_from_file_location('grader.py', grader)
        # grader = importlib.util.module_from_spec(spec)
        # spec.loader.exec_module(grader)
        # return grader.grade(flag)
        pass

    def save(self):
        self.desc_html = markdown2.markdown(
            self.desc, extras=['fenced-code-blocks']
        )
        self.hint_html = markdown2.markdown(
            self.hint, extras=['fenced-code-blocks']
        )
        self.full_clean()
        super(CTFProblem, self).save(**kwargs)


class Team(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
