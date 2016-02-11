from django.core import management
from django.core.management.base import BaseCommand


from ctflex.management.commands._common import add_no_input, pass_through_argument


class Command(BaseCommand):
    help = "Runs makemigrations, migrate, loadprobs, collectstatic"

    def add_arguments(self, parser):
        add_no_input(parser)

    def handle(self, **options):
        management.call_command('makemigrations')
        management.call_command('migrate')
        management.call_command('loadprobs', *pass_through_argument({
            '--no-input': not options['interactive'],
        }))
        management.call_command('collectstatic', '-c', *pass_through_argument({
            '--no-input': not options['interactive'],
        }))