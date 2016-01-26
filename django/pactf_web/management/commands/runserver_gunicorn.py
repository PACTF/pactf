from subprocess import call

from django.core.management.base import BaseCommand
from django.conf import settings

from pactf.constants import PROJECT_NAME


class Command(BaseCommand):
    help = """Run the Gunicorn app server"""

    def handle(self, **options):

        DJANGO_WSGI_MODULE = '{}.wsgi'.format(PROJECT_NAME)


        print("Trying to launch Gunicorn for project '{}'".format(PROJECT_NAME))

        if settings.USE_SOCKFILE:
            bind = 'unix:{}'.format(settings.SOCKFILE)
        else:
            bind = '{}:{}'.format(settings.IP, settings.PORT)

        # Note: Programs meant to be run under supervisor should not daemonize themselves
        call(((
            settings.GUNICORN,
            '{}:application'.format(DJANGO_WSGI_MODULE),
            '--name {}'.format(PROJECT_NAME),
            '--workers {}'.format(settings.NUM_WORKERS),
            '--user={}'.format(settings.USER),
            '--group={}'.format(settings.GROUP),
            '--log-level=debug',
            '--bind={}'.format(bind),
            '--log-file=-',
        )))
