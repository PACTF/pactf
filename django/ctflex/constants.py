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

LOGGER_NAME = APP_NAME

''' URLs '''

UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
API_NAMESPACE = 'api'

''' Problems '''

UUID_GENERATOR = uuid.uuid4
DEPS_PROBS_FIELD = 'probs'
DEPS_THRESHOLD_FIELD = 'threshold'
