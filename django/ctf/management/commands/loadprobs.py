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


PROBLEMS_DIR = settings.PROBLEMS_DIR
PROBLEMS_STATIC_DIR = settings.PROBLEMS_STATIC_DIR

PROBLEM_BASENAME = 'problem.yaml'
GRADER_BASENAME = 'grader.py'
STATIC_BASENAME = 'static'

NAME_FIELD = 'name'
PK_FIELD = 'id'


class Command(BaseCommand):
    help = "Adds/Updates problems from PROBLEM_DIR"

    def add_arguments(self, parser):
        pass

    def handle(self, **options):

        write = self.stdout.write
        errors = []

        write("Walking '{}'".format(PROBLEMS_DIR))
        for root in os.listdir(PROBLEMS_DIR):

            # Skip files
            if isfile(join(PROBLEMS_DIR, root)):
                continue

            # Ignore private dirs
            if root.startswith('_'):
                write("Ignoring '{}': Marked private with underscore".format(root))
                continue

            # Load problem file
            problem_filename = join(PROBLEMS_DIR, root, PROBLEM_BASENAME)
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
            static_from = join(PROBLEMS_DIR, root, STATIC_BASENAME)
            static_to = join(PROBLEMS_STATIC_DIR, data[NAME_FIELD])

            # Check if the problem already exists
            problem_id = data.get(PK_FIELD, '')
            query = CtfProblem.objects.filter(**{PK_FIELD: problem_id})
            try:
                if PK_FIELD in data and query.exists():

                    # If so, update the problem
                    write("Trying to update problem for '{}'".format(root))
                    query.update(**data)
                    for problem in query:
                        problem.save()

                    # Also, delete existing files
                    # TODO(Yatharth): Replace this with deleting all files in PROBLEMS_STATIC_DIR right in the beginning
                    if isdir(static_to):
                        write("Warning: Deleting existing staticfiles at '{}'".format(data[NAME_FIELD]))
                        shutil.rmtree(static_to)

                # Otherwise, create a new one
                else:
                    write("Trying to create problem for '{}'".format(root))
                    problem = CtfProblem(**data)
                    problem.save()

                # Either way, copy over any static files
                if isdir(static_from):
                    write("Trying to copy static files from '{}'".format(root))
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
