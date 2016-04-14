"""Define Python logging handlers, filters etc"""

import logging

from django.utils.log import AdminEmailHandler
from django.conf import settings
from django.core.cache import cache

from ctflex.constants import BASE_LOGGER_NAME

logger = logging.getLogger(BASE_LOGGER_NAME + '.' + __name__)


class ThrottledAdminEmailHandler(AdminEmailHandler):
    COUNTER_CACHE_KEY = 'email_admins_counter'

    def increment_counter(self):
        try:
            cache.incr(self.COUNTER_CACHE_KEY)
        except ValueError:
            cache.set(self.COUNTER_CACHE_KEY, 1, settings.EMAIL_RATELIMIT_SECONDS)
        return cache.get(self.COUNTER_CACHE_KEY)

    def emit(self, record):

        try:
            counter = self.increment_counter()
        except Exception:
            logger.warning("Throttling admin error email failed", exc_info=True)
        else:
            if counter > settings.EMAIL_RATELIMIT_NUMBER:
                logger.info("Throttling admin error email successful")
                return

        super(ThrottledAdminEmailHandler, self).emit(record)
