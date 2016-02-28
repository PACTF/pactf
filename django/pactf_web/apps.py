"""Define app config"""

from django.apps import AppConfig

from pactf_web import constants


class PactfWebConfig(AppConfig):
    name = constants.APP_NAME
