import textwrap

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

import yaml
from django.db import transaction

from ctflex.management.commands import helpers
from ctflex.models import Announcement, Competitor, CtfProblem, Window


class Command(BaseCommand):
    help = "Make an announcement from YAML "

    def add_arguments(self, parser):
        helpers.add_debug_argument(parser)
        helpers.add_clear_argument(parser)
        helpers.add_no_input_argument(parser)

        parser.add_argument('infile', type=open)

    def handle(self, *args, **options):

        helpers.debug_with_pdb(**options)

        # Parse file contents
        data = yaml.load(options['infile'])
        if not data:
            raise CommandError("Could not load announcement file")

        # Get window
        window_basename = data['window']
        try:
            data['window'] = Window.objects.get(codename=window_basename)
        except Window.DoesNotExist as err:
            self.stderr.write(
                "No window with codename {!r} found".format(window_basename))
            raise err

        # Extract problems
        if 'problems' in data:
            problems = data['problems']
            del data['problems']
        else:
            problems = ()

        # Check whether ID is already used
        id = data.get('id', None)
        if id and Announcement.objects.filter(id=id).exists():
            raise CommandError(
                "An existing announcement with the same ID {!r} exists".format(id))

        announcement = Announcement(**data)

        try:
            with transaction.atomic():

                try:
                    announcement.save()
                except ValidationError as err:
                    self.stderr.write("Validation failed")
                    raise err

                # Associate with problems
                announcement.problems.clear()
                for problem in problems:
                    announcement.problems.add(CtfProblem.objects.get(id=problem))
                announcement.validate_windows()

        except:
            self.stderr.write("Exception encountered; rolled back transaction")
            raise

        # Mark this announcement as unread by competitors
        # (This is outside the transaction manager as it is unlikely to fail
        #  but might take some time.)
        announcement.competitors.add(*Competitor.objects.all())

        self.stdout.write('Successfully created announcement: {}'.format(announcement))
