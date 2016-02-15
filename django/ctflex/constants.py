"""Hold app-specific constants

These constants can't just be stored in `models.py` because `apps.py` can't import `models.py`.
"""

APP_NAME = 'ctflex'
VERBOSE_NAME = 'CTFlex'

QUERY_LOGGER = APP_NAME + '.queries'

UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

LOGOUT_REDIRECT_URL = 'ctflex:index'
PASSWORD_CHANGE_REDIRECT_URL = 'ctflex:current_team'
