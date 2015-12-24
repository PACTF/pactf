import importlib.util, markdown2

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# TODO - make a JSONField or something similar to store the threshold dict
class Problem(models.Model):
    p_id = models.AutoField(primary_key=True)
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
        spec = importlib.util.spec_from_file_location('grader.py', self.grader)
        grader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grader)
        return grader.grade(flag)

    def save(self):
        self.desc_html = markdown2.markdown(
            self.desc, extras=['fenced-code-blocks']
        )
        self.hint_html = markdown2.markdown(
            self.hint, extras=['fenced-code-blocks']
        )
        self.full_clean()
        super(Problem, self).save()

class Team(models.Model):
    t_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
