"""Define app-specific constants

Having this file enables:
- Easily making a constant a setting in `ctflex.settings` and vice versa;
- Sharing constants between, for example, `apps.py` and `models.py` (`apps.py` can't import `models.py`);
"""

import uuid

''' App Metadata '''

APP_NAME = 'ctflex'
VERBOSE_NAME = 'CTFlex'

''' Logging '''

BASE_LOGGER_NAME = APP_NAME
CODE_LOGGER_NAME = BASE_LOGGER_NAME + ".code"
IP_LOGGER_NAME = BASE_LOGGER_NAME + ".ip"

''' URLs '''

UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
API_NAMESPACE = 'api'

''' Problems '''

UUID_GENERATOR = uuid.uuid4
DEPS_PROBS_FIELD = 'probs'
DEPS_THRESHOLD_FIELD = 'threshold'
COUNTDOWN_ENDTIME_KEY = 'countdown_endtime'
COUNTDOWN_MAX_MICROSECONDS_KEY = 'countdown_max_microseconds'
