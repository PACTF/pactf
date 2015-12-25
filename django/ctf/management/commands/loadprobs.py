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

            # Prepare problem dict
            data['grader'] = join(root + GRADER_BASENAME)
            problem = CtfProblem(**data)

            # Save problem
            try:
                problem.save()
            except ValidationError as err:
                write("Skipping '{}': Problem was invalid".format(root))
                errors.append(sys.exc_info())
                continue

            # We made it!
            write("Imported problem from '{}'".format(root))

        # Print stacktraces from before
        if errors:
            write("\nPrinting stacktraces of encountered exceptions")
            for err in errors:
                write(''.join(traceback.format_exception(*err)))


