from os.path import join, dirname, abspath

from django.core import management
from django.core.management.base import BaseCommand
from django.db import transaction

from ctflex.management.commands._common import add_no_input_argument, add_debug_argument, debug_with_pdb, filter_dict, \
    add_clear

BASE_DIR = join(dirname(dirname(dirname(abspath(__file__)))), 'fixtures')
PRE_PROBLEMS_FIXTURES = ('users.yaml', 'teams.yaml', 'competitors.yaml', 'windows.yaml',)
POST_PROBLEMS_FIXTURES = ('solves.yaml',)


class Command(BaseCommand):
    help = "Flush and migrate the database, and reload fixtures and problems (with static files)"

    def add_arguments(self, parser):
        add_debug_argument(parser)
        add_no_input_argument(parser)
        add_clear(parser)

    @staticmethod
    def load_fixture(fixture):
        print("Loading from {}".format(fixture))
        management.call_command('loaddata', join(BASE_DIR, fixture))

    def handle(self, **options):

        if options['debug']:
            debug_with_pdb()

        with transaction.atomic():

            management.call_command('flush', *filter_dict({
                '--no-input': not options['interactive'],
            }))
            management.call_command('makemigrations')
            management.call_command('migrate')

            for fixture in PRE_PROBLEMS_FIXTURES:
                self.load_fixture(fixture)

            management.call_command('loadprobs', *filter_dict({
                '--no-input': not options['interactive'],
                '--debug': options['debug'],
                '--clear': options['clear']
            }))
            self.stdout.write('')

            for fixture in POST_PROBLEMS_FIXTURES:
                self.load_fixture(fixture)

            management.call_command('collectstatic', '-c', *filter_dict({
                '--no-input': not options['interactive'],
            }))
