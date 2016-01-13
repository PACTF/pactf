from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs makemigrations, migrate, loadprobs, collectstatic"

    def add_arguments(self, parser):
        parser.add_argument('--noinput', '--no-input', '-n',
                            action='store_false', dest='interactive', default=True,
                            help="Do NOT prompt the user for input of any kind.")

    def handle(self, **options):
        interactive_args = () if options['interactive'] else ('--no-input',)

        management.call_command('makemigrations')
        management.call_command('migrate')
        management.call_command('loadprobs', *interactive_args)
        management.call_command('collectstatic', '-c', *interactive_args)
