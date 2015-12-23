import os, json

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from ctf.models import Problem

class Command(BaseCommand):
    help = (
        'Scans the directory specified in PROBLEMS_DIR for problem.json '
        'files. For each one it finds, it creates a new database table '
        'using the options given.'
    )

    def handle(self, *args, **options):
        for root, dirs, files in os.walk(settings.PROBLEMS_DIR):
            if 'problem.json' in files:
                data = json.load(open(os.path.join(root, 'problem.json')))
                p = Problem(**data)
                # TODO - copy all the static files into django's static dir
                # TODO - do something with a potential validation error
                p.save()
