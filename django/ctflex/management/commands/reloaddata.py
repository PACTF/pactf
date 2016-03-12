from os.path import join, dirname, abspath

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

    @staticmethod
    def load_fixture(fixture):
        print("Loading from {}".format(fixture))
        management.call_command('loaddata', join(BASE_DIR, fixture))

    def handle(self, **options):

        helpers.debug_with_pdb(**options)

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

                for fixture in POST_PROBLEMS_FIXTURES:
                    self.load_fixture(fixture)

        except Exception as err:
            self.stderr.write("Exception encountered; rolling back")
            raise CommandError(err)

        else:
            self.stdout.write("Successfully (re)loaded all fixtures and problems")
