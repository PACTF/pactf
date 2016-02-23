import sys
from os.path import join, dirname, abspath

from IPython.core import ultratb

from django.core import management
from django.core.management.base import BaseCommand

from ctflex.management.commands._common import add_no_input, add_debug, pass_through_argument, add_clear

BASE_DIR = join(dirname(dirname(dirname(abspath(__file__)))), 'fixtures')
PRE_PROBLEMS_FIXTURES = ('users.yaml', 'teams.yaml', 'competitors.yaml', 'windows.yaml',)
POST_PROBLEMS_FIXTURES = ('solves.yaml',)


class Command(BaseCommand):
    help = "Flush and reload fixtures and problems"

    def add_arguments(self, parser):
        add_no_input(parser)
        add_debug(parser)
        add_clear(parser)

    @staticmethod
    def load_fixture(fixture):
        print("Loading from {}".format(fixture))
        management.call_command('loaddata', join(BASE_DIR, fixture))


    def handle(self, **options):
        management.call_command('flush', *pass_through_argument({
            '--no-input': not options['interactive'],
        }))
        management.call_command('makemigrations')
        management.call_command('migrate')

        if options['debug']:
            sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)

        for fixture in PRE_PROBLEMS_FIXTURES:
            self.load_fixture(fixture)

        management.call_command('loadprobs', *pass_through_argument({
            '--no-input': not options['interactive'],
            '--debug': options['debug'],
            '--clear': options['clear']
        }))
        self.stdout.write('')

        for fixture in POST_PROBLEMS_FIXTURES:
            self.load_fixture(fixture)
