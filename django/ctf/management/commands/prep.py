from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs makemigrations, migrate, loadprobs, collectstatic"

    def handle(self, **options):
        management.call_command('makemigrations')
        management.call_command('migrate')
        management.call_command('loadprobs')
        management.call_command('collectstatic', '-c')
