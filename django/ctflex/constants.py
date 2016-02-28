"""Define app-specific constants

Having this file enables:
- Easily making a constant a setting in `ctflex.settings` and vice versa;
- Sharing constants between, for example, `apps.py` and `models.py` (`apps.py` can't import `models.py`);
"""

''' App Metadata '''

APP_NAME = 'ctflex'
VERBOSE_NAME = 'CTFlex'

''' Logging '''

QUERIES_LOGGER = APP_NAME + '.queries'
COMMANDS_LOGGER = APP_NAME + '.commands'

''' URLs '''

UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

''' Redirections '''

DEPS_PROBS_FIELD = 'probs'
DEPS_THRESHOLD_FIELD = 'threshold'
