from django.db import models

class Problem(models.Model):
    p_id = models.AutoField(primary_key=True)
    points = models.IntegerField()
    # XXX - Better to use FilePathField?
    grader = models.CharField(help_text='Path to the grading script')

class Team(models.Model):
    t_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    score = models.IntegerField()
