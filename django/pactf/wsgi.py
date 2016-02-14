"""Configure WSGI app"""

import envdir

from whitenoise.django import DjangoWhiteNoise

from pactf.constants import ENVDIR_PATH

envdir.open(ENVDIR_PATH)

from configurations.wsgi import get_wsgi_application

application = get_wsgi_application()
application = DjangoWhiteNoise(application)
