import os

from django.core.management.base import BaseCommand
from django.conf import settings

from pactf import constants


class Command(BaseCommand):
    help = """Run the Gunicorn app server"""

    def handle(self, **options):

        DJANGO_WSGI_MODULE = '{}.wsgi'.format(constants.PROJECT_NAME)

        print("Trying to launch Gunicorn for project '{}'".format(constants.PROJECT_NAME))

        if settings.GUNICORN_USE_SOCKFILE:
            bind = 'unix:{}'.format(settings.GUNICORN_SOCKFILE)
        else:
            bind = '{}:{}'.format(settings.GUNICORN_IP, settings.GUNICORN_PORT)

        # (Note: Programs meant to be run under supervisor should not daemonize themselves.)
        commands = (
            settings.GUNICORN_PATH,
            '{}:application'.format(DJANGO_WSGI_MODULE),
            '--name={}'.format(constants.PROJECT_NAME),
            '--workers={}'.format(settings.GUNICORN_NUM_WORKERS),
            '--user={}'.format(settings.GUNICORN_USER),
            '--group={}'.format(settings.GUNICORN_GROUP),
            '--log-level=debug',
            '--bind={}'.format(bind),
            '--log-file=-',
        )
        print(commands, flush=True)
        os.execvp(commands[0], commands)
