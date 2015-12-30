from os.path import join

from django.core import management
from django.core.management.base import BaseCommand

BASE_DIR = 'ctf/fixtures'
FIXTURES = ['users.yaml', 'teams.yaml', 'competitors.yaml']


class Command(BaseCommand):
    help = "Flushes and reloads fixtures"

    def handle(self, **options):
        management.call_command('flush')
        for fixture in FIXTURES:
            management.call_command('loaddata', join(BASE_DIR, fixture))
