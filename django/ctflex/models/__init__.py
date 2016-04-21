"""Import actual models and then connect signals

Such a separation exists to avoid circular imports.
"""

import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out

from ctflex.models.models import *

from ctflex import signals
from ctflex import loggers
from ctflex import settings
from ctflex.constants import BASE_LOGGER_NAME

logger = logging.getLogger(BASE_LOGGER_NAME + '.' + __name__)

signals.unique_connect(user_logged_in, loggers.log_login)
signals.unique_connect(user_logged_out, loggers.log_logout)

logger.debug("captcha {}/{}".format(settings.NORECAPTCHA_SITE_KEY, settings.NORECAPTCHA_SECRET_KEY))
