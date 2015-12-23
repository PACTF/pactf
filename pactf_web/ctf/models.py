import importlib.util as iutil
from django.db import models

class Problem(models.Model):
    p_id = models.AutoField(primary_key=True)
    points = models.IntegerField()
    name = models.CharField(unique=True, max_length=20)
    desc = models.TextField()
    hint = models.TextField(default='')
    grader = models.FilePathField(help_text='Path to the grading script')

    def grade(self, flag):
        spec = importlib.util.spec_from_file_location('grader.py', grader)
        grader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grader)
        return grader.grade(flag)

class Team(models.Model):
    t_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
