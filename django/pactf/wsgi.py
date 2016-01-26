"""WSGI config
"""

from os.path import dirname, join, abspath

import envdir

from pactf.constants import ENVDIR_PATH


envdir.open(ENVDIR_PATH)

from configurations.wsgi import get_wsgi_application

application = get_wsgi_application()
