"""Define app-specific constants

These constants can't just be stored in `models.py` because `apps.py` can't import `models.py`.

Note: It might make sense to move some of the below constants to the settings.py file.
"""

import zlib

from django.conf import settings

''' Meta info '''

APP_NAME = 'ctflex'
VERBOSE_NAME = 'CTFlex'

SUPPORT_EMAIL = 'ctflex2@gmail.com'

''' Logging '''

QUERY_LOGGER = APP_NAME + '.queries'

''' URLs '''

UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

''' Window Names '''

OVERALL_WINDOW_NAME = 'overall'

''' Session '''

WINDOW_SESSION_KEY = 'window_id'

''' Redirections '''

# (LOGIN_REDIRECT_URL is in settings.py because Django code uses it.)
WINDOW_CHANGE_URL = 'ctflex:game'
LOGOUT_REDIRECT_URL = 'ctflex:index'
TEAM_CHANGE_REDIRECT_URL = 'ctflex:current_team'
INVALID_STATE_REDIRECT_URL = 'ctflex:index'

''' Security '''

PROBLEM_SALT = 'ctfproblems'

''' Problem Dependencies '''

DEPS_PROBS_FIELD = 'probs'
DEPS_THRESHOLD_FIELD = 'threshold'

''' Problem folder structure '''

PROBLEM_BASENAME = 'problem.yaml'
GRADER_BASENAME = 'grader.py'
GENERATOR_BASENAME = 'generator.py'
STATIC_BASENAME = 'static'
UUID_BASENAME = '.uuid'
UUID_BACKUP_BASENAME = '.uuid.rejected'

''' Registration Template Context '''

TEAM_STATUS_NAME = 'team-status'
TEAM_STATUS_NEW = 'new'
TEAM_STATUS_OLD = 'old'
