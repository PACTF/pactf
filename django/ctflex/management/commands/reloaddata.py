import os
import glob
from os.path import join, dirname, abspath, isfile

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ctflex.management.commands import helpers

BASE_DIR = join(dirname(dirname(dirname(abspath(__file__)))), 'fixtures')
PRE_PROBLEMS_FIXTURES = ('users.yaml', 'teams.yaml', 'competitors.yaml', 'windows.yaml',)
POST_PROBLEMS_FIXTURES = ('solves.yaml',)


class Command(BaseCommand):
    help = "Flush and migrate the database, and reload fixtures and problems (with static files)"

    def add_arguments(self, parser):
        helpers.add_debug_argument(parser)
        helpers.add_no_input_argument(parser)
        helpers.add_clear_argument(parser)
        parser.add_argument('--skiplater',
                            action='store_true', dest='skiplater', default=False,
                            help="Don’t load the solves fixture or announcements")

    @staticmethod
    def load_fixture(fixture):
        print("Loading from {}".format(fixture))
        management.call_command('loaddata', join(BASE_DIR, fixture))

    def handle(self, **options):

        helpers.debug_with_pdb(**options)

        self.stdout.write("Beginning transaction\n")

        try:
            with transaction.atomic():

                management.call_command('flush', *helpers.filter_dict({
                    '--no-input': not options['interactive'],
                }))
                management.call_command('makemigrations')
                management.call_command('migrate')

                for fixture in PRE_PROBLEMS_FIXTURES:
                    self.load_fixture(fixture)

                # (loadprobs will call collectstatic.)
                management.call_command('loadprobs', *helpers.filter_dict({
                    '--no-input': not options['interactive'],
                    '--debug': options['debug'],
                    '--clear': options['clear']
                }))
                self.stdout.write('')

                if not options['skiplater']:

                    for fixture in POST_PROBLEMS_FIXTURES:
                        self.load_fixture(fixture)

                    announcements_dir = join(BASE_DIR, 'announcements')
                    for basename in glob.glob(os.path.join(announcements_dir, '*.yaml')):
                        print(basename)
                        path = join(announcements_dir, basename)
                        if isfile(path):
                            management.call_command('announce', path)

        except Exception as err:
            self.stderr.write("Unforeseen exception encountered; rolled back transaction")
            raise CommandError(err)
        else:
            self.stdout.write("Successfully (re)loaded all fixtures and problems")
