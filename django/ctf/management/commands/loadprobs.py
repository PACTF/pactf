import os
import re
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
from ctf.constants import UUID_REGEX

PROBLEMS_DIR = settings.PROBLEMS_DIR
PROBLEMS_STATIC_DIR = settings.PROBLEMS_STATIC_DIR

PROBLEM_BASENAME = 'problem.yaml'
GRADER_BASENAME = 'grader.py'
STATIC_BASENAME = 'static'
UUID_BASENAME = '.uuid'
UUID_BACKUP_BASENAME = '.uuid.rejected'

PK_FIELD = 'id'


class Command(BaseCommand):
    help = "Adds/Updates problems from PROBLEM_DIR"

    def add_arguments(self, parser):
        parser.add_argument('--noinput', '--no-input', '-n',
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
            write("Deleting all files in the intermediate location\n\n")
            shutil.rmtree(PROBLEMS_STATIC_DIR)

        errors = []

        write("Walking '{}'".format(PROBLEMS_DIR))
        for root in os.listdir(PROBLEMS_DIR):
            write("")

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
            data['grader'] = join(root, GRADER_BASENAME)

            # Clean and warn about integer IDs
            if 'id' in data:
                self.stderr.write(textwrap.dedent("""\
                    Warning: Integer IDs are obsolete and will be ignored.
                    Create/modify a {} file in folder '{}' instead.\
                    """.format(UUID_BASENAME, root)))
                del data['id']

            # Check for and validate existing UUID file
            uuid_path = join(PROBLEMS_DIR, root, UUID_BASENAME)
            if isfile(uuid_path):
                with open(uuid_path) as uuid_file:
                    uuid = uuid_file.read().strip()
                    data[PK_FIELD] = uuid

                if not re.match('{}$'.format(UUID_REGEX), uuid):
                    write("Error: UUID File did not match the expected format '{}'".format(UUID_REGEX))
                    uuid = None

                    write("Backing up and deleting existing UUID file")
                    backip_uuid_path = join(PROBLEMS_DIR, root, UUID_BACKUP_BASENAME)
                    shutil.move(uuid_path, backip_uuid_path)
            else:
                uuid = None

            query = CtfProblem.objects.filter(**{PK_FIELD: uuid})
            try:

                # If so, update the problem
                if uuid and query.exists():
                    write("Trying to update problem for '{}'".format(root))
                    # TODO(Yatharth): Have single problem, keep problem.save() for later for  ValidationError
                    # Consider using exception handling and __dict__.update or update_or_create)
                    query.update(**data)
                    for problem in query:
                        problem.save()

                # Otherwise, create a new one
                else:
                    write("Trying to create problem for '{}'".format(root))
                    problem = CtfProblem(**data)
                    problem.save()

                    # Save the UUID to a file
                    uuid = str(problem.id)
                    write("Creating a UUID file for '{}'".format(root))
                    with open(uuid_path, 'w') as uuid_file:
                        uuid_file.write(uuid)

            # Catch validation errors
            except ValidationError:
                write("Validation failed for '{}'".format(root))
                errors.append(sys.exc_info())
                continue

            # Either way, copy over any static files
            try:
                static_from = join(PROBLEMS_DIR, root, STATIC_BASENAME)
                static_to = join(PROBLEMS_STATIC_DIR, str(uuid))
                if isdir(static_from):
                    write("Trying to copy static files from '{}'".format(root))
                    shutil.copytree(static_from, static_to)

            except (shutil.Error, IOError):
                write("Unable to copy static files for '{}'".format(root))
                errors.append(sys.exc_info())
                continue

            # We made it!
            write("Successfully imported problem for '{}'".format(root))

        # Print the stack traces from before
        if errors:
            write("\nPrinting stacktraces of encountered exceptions")
            for err in errors:
                write(''.join(traceback.format_exception(*err)))
