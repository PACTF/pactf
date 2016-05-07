from django.core import management
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ctflex import constants
from ctflex import settings
from ctflex.management.commands import helpers
from ctflex.models import Team, Competitor

class Command(BaseCommand):
    help = "Dump teams' email addresses."

    def add_arguments(self, parser):
        parser.add_argument('team_list', type=str)

    def handle(self, **options):
        if not options['team_list']:
            raise CommandError('Please specify a list of teams to dump.')
        write = self.stdout.write
        for team in open(options['team_list']):
            write(team)
            for member in Team.objects.get(name=team).competitor_set.all():
                write(member.user.email)
