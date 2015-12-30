from os.path import join

from django.core import management
from django.core.management.base import BaseCommand


BASE_DIR = 'ctf/fixtures'
FIXTURES = ('test.yaml',)

class Command(BaseCommand):
    help = "Flushes and reloads fixtures"

    def handle(self, **options):
        management.call_command('flush')
        fixture_args = ' '.join(join(BASE_DIR, fixture) for fixture in FIXTURES)
        management.call_command('loaddata', fixture_args)
