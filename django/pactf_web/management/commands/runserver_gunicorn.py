from subprocess import call

from django.core.management.base import BaseCommand
from django.conf import settings

from pactf import constants


class Command(BaseCommand):
    help = """Run the Gunicorn app server"""

    def handle(self, **options):

        DJANGO_WSGI_MODULE = '{}.wsgi'.format(constants.PROJECT_NAME)

        print("Trying to launch Gunicorn for project '{}'".format(constants.PROJECT_NAME))

        if settings.USE_SOCKFILE:
            bind = 'unix:{}'.format(settings.SOCKFILE)
        else:
            bind = '{}:{}'.format(settings.IP, settings.PORT)

        # (Note: Programs meant to be run under supervisor should not daemonize themselves.)
        call(((
            settings.GUNICORN,
            '{}:application'.format(DJANGO_WSGI_MODULE),
            '--name {}'.format(constants.PROJECT_NAME),
            '--workers {}'.format(settings.NUM_WORKERS),
            '--user={}'.format(settings.USER),
            '--group={}'.format(settings.GROUP),
            '--log-level=debug',
            '--bind={}'.format(bind),
            '--log-file=-',
        )))
