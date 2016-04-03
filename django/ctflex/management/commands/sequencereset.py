import os
import textwrap

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils.six import StringIO

from ctflex.management.commands import helpers


class Command(BaseCommand):
    help = "Reset sequence IDs"

    def add_arguments(self, parser):
        helpers.add_debug_argument(parser)
        helpers.add_no_input_argument(parser)

    def handle(self, *args, **options):
        helpers.debug_with_pdb(**options)

        os.environ['DJANGO_COLORS'] = 'nocolor'

        commands_buffer = StringIO()
        for app in apps.get_app_configs():
            call_command('sqlsequencereset', app.label, stdout=commands_buffer)
        commands = commands_buffer.getvalue()

        message = textwrap.dedent("""\
            You have requested to reset sequences for all Django apps.
            The following commands will be run:

            {}

            Are you sure you want to do this?

            Type 'yes' to continue, or 'no' to cancel:\
            """).format(textwrap.indent(commands, '\t'))
        if options['interactive'] and input(message) != "yes":
            raise CommandError("Resetting sequences cancelled.")

        cursor = connection.cursor()
        cursor.execute(commands)
