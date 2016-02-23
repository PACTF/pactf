import sys, traceback

import yaml
from IPython.core import ultratb
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from ctflex.management.commands._common import add_debug
from ctflex.models import Announcement, Competitor, CtfProblem

class Command(BaseCommand):
    help = "Make an announcement."

    def add_arguments(self, parser):
        add_debug(parser)
        parser.add_argument('announcement_file', type=open)

    def handle_error(self, err):
        self.errored = True
        if self.debug:
            raise err
        else:
            self.stdout.write(''.join(traceback.format_exception(*sys.exc_info())))

    def handle(self, *args, **options):
        write = self.stdout.write
        self.debug = options['debug']
        if self.debug:
            sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)
        data = yaml.load(options['announcement_file'])
        try:
            if 'problems' not in data: data['problems'] = []
            probs = data['problems']
            del data['problems']
            pre_existing = False
            # check if announcement exists
            if Announcement.objects.get(pk=data['id']):
                pre_existing = True
                ann = Announcement.objects.get(pk=data['id'])
            # otherwise, create the announcement
            else:
                ann = Announcement(**data)
                ann.save()
            for prob in probs:
                ann.problems.add(CtfProblem.objects.get(pk=prob))
            # Push this announcement to each competitor's unread announcements queue
            for competitor in Competitor.objects.all():
                ann.competitor_set.add(competitor)
            write(
                'Successfully %s announcement %s' %
                ('updated' if pre_existing else 'created', ann.title)
            )
        except ValidationError as e:
            write('Improperly formatted announcement.')
            self.handle_error(e)
