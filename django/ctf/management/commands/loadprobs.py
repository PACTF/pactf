import os
import sys
import traceback
import shutil
from os.path import join, isfile, isdir

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

import yaml

from ctf.models import CtfProblem


class Command(BaseCommand):
    help = "Adds/Updates problems from PROBLEM_DIR"

    def add_arguments(self, parser):
        pass

    def handle(self, **options):
        BASEDIR = settings.PROBLEMS_DIR
        STATIC_DIRNAME = join(settings.STATIC_ROOT, 'problems')
        STATIC_BASENAME = 'static'
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

            # Create the directories we'd copy static files to and from
            static_from = join(BASEDIR, root, STATIC_BASENAME)
            static_to = join(STATIC_DIRNAME, root)

            # Check if the problem already exists
            problem_id = data.get(PK_FIELD, '')
            query = CtfProblem.objects.filter(**{PK_FIELD: problem_id})
            try:
                if PK_FIELD in data and query.exists():

                    # Update problem
                    write("Trying to update problem for '{}'".format(root))
                    query.update(**data)
                    for problem in query:
                        problem.save()

                    # Delete existing files
                    if isdir(static_to):
                        write("Warning: Deleting existing staticfiles at '{}'".format(static_to))
                        shutil.rmtree(static_to)

                # Otherwise, create a new one
                else:
                    write("Trying to create problem for '{}'".format(root))
                    problem = CtfProblem(**data)
                    problem.save()

                # Either way, copy over any static files
                print(static_to)
                if isdir(static_from):
                    write("Trying to copy static files from '{}'".format(static_from))
                    shutil.copytree(static_from, static_to)

            # Output success or failure
            except ValidationError:
                write("Validation failed for '{}'".format(root))
                errors.append(sys.exc_info())
                continue
            except (shutil.Error, IOError):
                write("Unable to copy static files for '{}'".format(root))
                errors.append(sys.exc_info())
                continue
            else:
                write("Successfully imported problem for '{}'".format(root))

        # Print the stack traces from before
        if errors:
            write("\nPrinting stacktraces of encountered exceptions")
            for err in errors:
                write(''.join(traceback.format_exception(*err)))
