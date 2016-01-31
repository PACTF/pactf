from os.path import join

from django.core import management
from django.core.management.base import BaseCommand

BASE_DIR = 'ctflex/fixtures'
FIXTURES = ['users.yaml', 'teams.yaml', 'competitors.yaml', 'windows.yaml']


class Command(BaseCommand):
    help = "Flushes and reloads fixtures and problems"

    def add_arguments(self, parser):
        parser.add_argument('--noinput', '--no-input', '-n',
                            action='store_false', dest='interactive', default=True,
                            help="Do NOT prompt the user for input of any kind.")

    def handle(self, **options):
        interactive_args = () if options['interactive'] else ('--no-input',)
        management.call_command('flush', *interactive_args)
        for fixture in FIXTURES:
            management.call_command('loaddata', join(BASE_DIR, fixture))
