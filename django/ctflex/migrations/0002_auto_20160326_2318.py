# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-27 03:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctflex', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ctfproblem',
            name='generator',
            field=models.FilePathField(blank=True, help_text="Basename of the problem's generator script in PROBLEMS_DIR", match='^.*\\.py$', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='ctfproblem',
            name='grader',
            field=models.FilePathField(help_text="Basename of the problem's grading script in PROBLEMS_DIR", match='^.*\\.py$', max_length=200),
        ),
    ]