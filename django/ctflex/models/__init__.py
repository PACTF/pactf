"""Import actual models and then connect signals

Such a separation exists to avoid circular imports.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out

from ctflex.models.models import *
from ctflex import signals
from ctflex import loggers

signals.unique_connect(user_logged_in, loggers.log_login)
signals.unique_connect(user_logged_out, loggers.log_logout)
