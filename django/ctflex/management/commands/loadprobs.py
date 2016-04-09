import os
import re
import shutil
import sys
import textwrap
import traceback
from os.path import join, isfile, isdir

from django.core import management
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

import yaml
import yaml.parser

from ctflex import constants
from ctflex import settings
from ctflex.management.commands import helpers
from ctflex.models import CtfProblem, Window

PROBLEMS_DIR = settings.PROBLEMS_DIR
PROBLEMS_STATIC_DIR = settings.PROBLEMS_STATIC_DIR

PROBLEMFILE_BASENAME = 'problem.yaml'
GRADER_BASENAME = 'grader.py'
GENERATOR_BASENAME = 'generator.py'
STATICFOLDER_BASENAME = 'static'
UUID_BASENAME = '.uuid'
UUID_BACKUP_BASENAME = '.uuid.rejected'

PK_FIELD = 'id'


class Command(BaseCommand):
    help = "Load problems atomically (with static files)"

    def add_arguments(self, parser):
        helpers.add_no_input_argument(parser)
        helpers.add_debug_argument(parser)
        helpers.add_clear_argument(parser)

    def walk(self, directory):
        """Yield sub-directories that don't begin with an underscore"""

        # Walk over the directory
        self.stdout.write("Walking directory '{}'".format(directory))
        for basename in os.listdir(directory):
            self.stdout.write("")
            path = join(directory, basename)

            # Skip files
            if isfile(path):
                self.stdout.write("Ignoring '{}': Is file".format(basename))
                continue

            # Ignore private dirs
            if basename.startswith('_') or basename.startswith('.'):
                self.stdout.write("Ignoring '{}': Marked private with underscore or dot".format(basename))
                continue

            yield basename, path

    def handle_error(self, err):

        self.errored = True
        if self.debug:
            raise err
        else:
            self.stdout.write(''.join(traceback.format_exception(*sys.exc_info())))

    def process_problem_folder(self, *, prob_path, prob_basename, window_basename):

        prob_identifier = "{}/{}".format(window_basename, prob_basename)

        # Load problem file
        problem_filename = join(prob_path, PROBLEMFILE_BASENAME)
        try:
            with open(problem_filename) as problem_file:
                data = yaml.load(problem_file)
        except (IsADirectoryError, FileNotFoundError) as err:
            self.stderr.write("Skipping '{}': No problems file found".format(prob_identifier))
            self.handle_error(err)
            return
        except yaml.parser.ParserError as err:
            self.stderr.write("Skipping '{}': Parser error".format(prob_identifier))
            self.handle_error(err)
            return

        # Set paths
        data['grader'] = join(prob_path, GRADER_BASENAME)
        if 'dynamic' in data:
            if data['dynamic']:
                data['generator'] = join(prob_path, GENERATOR_BASENAME)
            del data['dynamic']

        # Clean and warn about integer IDs
        if 'id' in data:
            self.stderr.write(textwrap.dedent("""\
                    Warning: Integer IDs are obsolete and will be ignored.
                    Create/modify a {} file in folder '{}' instead.\
                    """.format(UUID_BASENAME, prob_identifier)))
            del data['id']

        # Check for and validate existing UUID file
        uuid_path = join(prob_path, UUID_BASENAME)
        if isfile(uuid_path):
            with open(uuid_path) as uuid_file:
                uuid = uuid_file.read().strip()
                data[PK_FIELD] = uuid

            if not re.match('{}$'.format(constants.UUID_REGEX), uuid):
                self.stderr.write(
                    "Error: UUID File did not match the expected format '{}'".format(
                        constants.UUID_REGEX))
                uuid = None

                self.stderr.write("Backing up and deleting existing UUID file")
                backip_uuid_path = join(prob_path, UUID_BACKUP_BASENAME)
                shutil.move(uuid_path, backip_uuid_path)

        # Else, generate a UUID
        else:
            uuid = str(constants.UUID_GENERATOR())
            self.stdout.write("Creating a UUID file for '{}'".format(prob_identifier))
            with open(uuid_path, 'w') as uuid_file:
                uuid_file.write(uuid)

        # Add window and add defaults
        try:
            data['window'] = Window.objects.get(codename=window_basename)
        except Window.DoesNotExist as err:
            self.stderr.write("No window named {!r} found".format(window_basename))
            self.handle_error(err)
            return

        # Configure fields
        data['id'] = uuid
        data.setdefault('generator', None)
        data['description_raw'] = data.pop('description', '')
        data['hint_raw'] = data.pop('hint', '')

        # Remove extra fields
        for attr in set(data.keys()) - set(field.name for field in CtfProblem._meta.get_fields()):
            del data[attr]

        # If problem exists, update it
        query = CtfProblem.objects.filter(**{PK_FIELD: uuid})
        if uuid and query.exists():
            self.stdout.write("Trying to update problem for '{}'".format(prob_identifier))
            problem = query.get()
            for attr, value in data.items():
                setattr(problem, attr, value)

        # Otherwise, create a new problem
        else:
            self.stdout.write("Trying to create problem for '{}'".format(prob_identifier))
            problem = CtfProblem(**data)

        # Validate and save to list
        try:
            problem.clean()
        except ValidationError as err:
            self.stderr.write("Validation failed for '{}'".format(prob_identifier))
            self.handle_error(err)
            return

        self.processed_problems.append(problem)

        # Copy over any static files
        try:
            static_from = join(prob_path, STATICFOLDER_BASENAME)
            static_to = join(PROBLEMS_STATIC_DIR, str(uuid))

            if isdir(static_from):
                self.stdout.write("Trying to copy static files from '{}'".format(prob_identifier))
                shutil.copytree(static_from, static_to)

        except (shutil.Error, IOError) as err:
            self.stderr.write("Unable to copy static files for '{}'".format(prob_identifier))
            self.handle_error(err)
            return

        # We made it!
        self.stdout.write("Validated problem for '{}'".format(prob_identifier))

    def delete_unprocessed(self, options):
        """Delete existing problems that were not updated if clear option was given

        (This action is so dangerous that even passing in '--no-input'
        does not automatically approve it.)
        """

        unprocessed_problems = CtfProblem.objects.exclude(
            pk__in=[problem.id for problem in self.processed_problems]).all()

        if options['clear'] and unprocessed_problems:

            affirmative_answer = "yes_this_is_dangerous"
            message = textwrap.dedent("""\
                    You have requested to delete all pre-existing problems that were not updated.
                    Please review the list of problems to be deleted.

                        {}

                    This will DELETE ALL THE LISTED PROBLEMS!
                    Are you sure you want to do this?

                    Type {!r} to continue, or 'no' to cancel:\
                    """.format(', '.join(map(str, unprocessed_problems)), affirmative_answer))

            if not options['interactive']:
                self.stderr.write("WARNING: You can only delete pre-existing problems in interactive mode\n"
                                  "(i.e., without the --no-input option)")

            elif input(message) != affirmative_answer:
                self.stderr.write("Did not receive response {!r}; therefore:\n"
                                  "NOT deleting the above-listed problems"
                                  .format(affirmative_answer))

            else:
                self.stdout.write("\nDeleting all unprocessed problems\n\n")
                for problem in unprocessed_problems:
                    problem.delete()

    def handle(self, **options):

        write = self.stdout.write
        self.processed_problems = []

        # Initialize error handling
        self.errored = False
        self.debug = options[helpers.DEBUG_OPTION_NAME]
        helpers.debug_with_pdb(**options)

        # Delete any existing files after confirmation
        if isdir(PROBLEMS_STATIC_DIR):
            message = textwrap.dedent("""\
                You have requested to load problems into the database and collect static files
                to the intermediate location as specified in your settings:

                    {}

                This will DELETE ALL FILES in this location!
                Are you sure you want to do this?

                Type 'yes' to continue, or 'no' to cancel:\
                """.format(PROBLEMS_STATIC_DIR))
            if options['interactive'] and input(message) != "yes":
                raise CommandError("Loading problems cancelled.")
            write("Deleting all files in the intermediate location\n\n")
            shutil.rmtree(PROBLEMS_STATIC_DIR)
        os.makedirs(PROBLEMS_STATIC_DIR, exist_ok=True)

        # Load problems
        for window_basename, window_path in self.walk(PROBLEMS_DIR):
            for prob_basename, prob_path in self.walk(window_path):
                self.process_problem_folder(
                    window_basename=window_basename,
                    prob_basename=prob_basename,
                    prob_path=prob_path
                )

        # Stop if errors were encountered
        if self.errored:
            write("")
            raise CommandError("Exception(s) were encountered; database was not modified")

        # Collect all static files to final location
        write("")
        write("Collecting static files to final location")
        management.call_command('collectstatic', *helpers.filter_dict({
            '--no-input': not options['interactive'],
            '--clear': options['clear'],
        }))


        self.stdout.write("Beginning transaction to actually save problems\n")
        try:

            # Actually load problems
            with transaction.atomic():
                print('POINT A')
                print(self.processed_problems)
                print('POINT B')
                for problem in self.processed_problems:
                    print("Saving {} to window {}".format(problem, problem.window))
                    problem.save()

            # Delete unprocessed problems
            self.delete_unprocessed(options)

        except Exception as err:
            self.stderr.write("Unforeseen exception encountered while saving problems; rolled back transaction")
            raise CommandError(err)
