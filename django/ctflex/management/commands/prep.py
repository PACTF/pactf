from django.core import management
from django.core.management.base import BaseCommand

from ctflex.management.commands._common import add_no_input_argument, filter_dict


class Command(BaseCommand):
    help = "Migrates loadprobs, collectstatic"

    def add_arguments(self, parser):
        add_no_input_argument(parser)

    def handle(self, **options):
        management.call_command('makemigrations')
        management.call_command('migrate')
        management.call_command('loadprobs', *filter_dict({
            '--no-input': not options['interactive'],
        }))
        management.call_command('collectstatic', '-c', *filter_dict({
            '--no-input': not options['interactive'],
        }))
