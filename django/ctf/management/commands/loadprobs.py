import os
import sys
import traceback
from os.path import join, isfile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

import yaml

from ctf.models import CtfProblem

class Command(BaseCommand):
    help = (
        'Scans the directory specified in PROBLEMS_DIR for problem.json '
        'files. For each one it finds, it creates a new database table '
        'using the options given.'
    )

    def add_arguments(self, parser):
        pass

    def handle(self, **options):
        # TODO(Yatharth): update if problem already in database
        # TODO(Yatharth): ask for confirmation if updating
        # TODO(Cam): Copy static files

        BASEDIR = settings.PROBLEMS_DIR
        PROBLEM_BASENAME = 'problem.yaml'
        GRADER_BASENAME = 'grader.py'
        PK_FIELD = 'id'

        write = self.stdout.write

        errors = []

        write("Walking '{}'".format(BASEDIR))
        for root in os.listdir(BASEDIR):

            # Skip files
            if isfile(join(BASEDIR, root)):
                continue

            # Ignore private dirs
            if root.startswith('_'):
                write("Ignoring '{}': Marked private with underscore".format(root))
                continue

            # Load problem file
            problem_filename = join(BASEDIR, root, PROBLEM_BASENAME)
            try:
                with open(problem_filename) as problem_file:
                    data = yaml.load(problem_file)
            except (IsADirectoryError, FileNotFoundError):
                write("Skipping '{}': No problems file found".format(root))
                errors.append(sys.exc_info())
                continue
            else:
                data['grader'] = join(root, GRADER_BASENAME)

            # Check it problem already exists
            problem_id = data.get(PK_FIELD, '')
            query = CtfProblem.objects.filter(**{PK_FIELD: problem_id})
            try:
                if PK_FIELD in data and query.exists():
                    write("Trying to update problem for '{}'".format(root))
                    query.update(**data)

                # Otherwise, create a new one
                else:
                    write("Trying to create problem for '{}'".format(root))
                    problem = CtfProblem(**data)
                    problem.save()

            # Output success or failure
            except ValidationError:
                write("Validation failed for '{}'".format(root))
                errors.append(sys.exc_info())
                continue
            else:
                write("Successfully imported problem for '{}'".format(root))

        # Print stacktraces from before
        if errors:
            write("\nPrinting stacktraces of encountered exceptions")
            for err in errors:
                write(''.join(traceback.format_exception(*err)))


