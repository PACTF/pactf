import os
import sys
import textwrap
import traceback
import shutil
from os.path import join, isfile, isdir

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

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
        parser.add_argument('--noinput', '--no-input',
            action='store_false', dest='interactive', default=True,
            help="Do NOT prompt the user for input of any kind.")

    def handle(self, **options):

        write = self.stdout.write

        # Delete any existing files after confirmation
        if isdir(PROBLEMS_STATIC_DIR):
            message = textwrap.dedent("""\
                You have requested to load problems into the database and collect static files
                to the intermediate     location as specified in your settings:

                    {}

                This will DELETE ALL FILES in this location!
                Are you sure you want to do this?

                Type 'yes' to continue, or 'no' to cancel:\
                """.format(PROBLEMS_STATIC_DIR))
            if options['interactive'] and input(message) != "yes":
                raise CommandError("Loading problems cancelled.")
            write("Deleting all files in the intermediate location\n")
            shutil.rmtree(PROBLEMS_STATIC_DIR)

        errors = []

        write("Walking '{}'\n".format(PROBLEMS_DIR))
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

            # Check if the problem already exists
            problem_id = data.get(PK_FIELD, '')
            query = CtfProblem.objects.filter(**{PK_FIELD: problem_id})
            try:

                # If so, update the problem
                if PK_FIELD in data and query.exists():
                    write("Trying to update problem for '{}'".format(root))
                    query.update(**data)
                    for problem in query:
                        problem.save()

                # Otherwise, create a new one
                else:
                    write("Trying to create problem for '{}'".format(root))
                    problem = CtfProblem(**data)
                    problem_id = problem.id
                    problem.save()

                # Either way, copy over any static files
                static_from = join(PROBLEMS_DIR, root, STATIC_BASENAME)
                static_to = join(PROBLEMS_STATIC_DIR, str(problem_id))
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

            write('')

        # Print the stack traces from before
        if errors:
            write("\nPrinting stacktraces of encountered exceptions")
            for err in errors:
                write(''.join(traceback.format_exception(*err)))
