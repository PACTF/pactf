from django.core.management.base import BaseCommand

from ctflex import commands


class Command(BaseCommand):
    help = "Refresh all scoreboards"

    def handle(self, *args, **options):
        commands.update_board()
