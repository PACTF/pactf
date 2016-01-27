from os.path import join

from configurations import Configuration, values

from pactf.constants import BASE_DIR


# TODO(Yatharth): Prefix attributes and set django-configurations prefix appropriately

class Django(Configuration):
    INSTALLED_APPS = [
        # Django Defaults
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        # Django Extensions
        'django.contrib.postgres',

        # Django 3rd-party
        'django_extensions',
        'debug_toolbar',

        # Python 3rd-party
        'yaml',

        # Local
        # Note: pactf_web comes before ctflex to override the latter's templates
        'pactf_web',
        'ctflex',
    ]

    MIDDLEWARE_CLASSES = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.middleware.security.SecurityMiddleware',
    )

    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )

    ROOT_URLCONF = 'pactf.urls'

    WSGI_APPLICATION = 'pactf.wsgi.application'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    # URL to serve static files at
    STATIC_URL = '/static/'

    # Make connections persistent
    CONN_MAX_AGE = 60 * 60

    # Auth URLs
    LOGIN_URL = 'login'
    LOGOUT_URL = 'logout'
    LOGIN_REDIRECT_URL = 'ctflex:index'

    # Internationalization
    LANGUAGE_CODE = 'en-us'
    TIME_ZONE = 'America/New_York'
    USE_I18N = True
    USE_L10N = True
    USE_TZ = True

    # Database
    # (Postgres is recommended.)
    DATABASES = values.DatabaseURLValue(environ_required=True)

    # Where to finally collect static files to
    # (Point your server (nginx, Apache etc.) to serve from this folder directly.)
    STATIC_ROOT = join(BASE_DIR, 'static')

    # Where all to collect static files from
    STATICFILES_DIRS = values.ListValue([])

    SECRET_KEY = values.SecretValue()


class Gunicorn:
    # As whom Gunicorn should run the server
    USER = values.Value()
    GROUP = values.Value()

    # Path to Gunicorn
    GUNICORN = values.PathValue('~/.virtualenvs/pactf/bin/gunicorn')

    # Whether to use a socket or serve directly to an address
    USE_SOCKFILE = values.BooleanValue(False)

    # Socket to communicate with
    SOCKFILE = values.PathValue(join(BASE_DIR, 'run', 'gunicorn.sock'), check_exists=False)

    # Url to directly serve to
    IP = values.IPValue('127.0.0.1')
    PORT = values.IntegerValue(8001)

    # Number of worker processes Gunicorn should spawn
    NUM_WORKERS = values.IntegerValue(3)


class CTFlex(Django):
    # Where to import problems from
    PROBLEMS_DIR = join(BASE_DIR, 'ctfproblems')

    # Intermediate folder for problem static files
    # (`manage.py loadprobs` will collect files to here, and `manage.py collectstatic` will collect from here to static.)
    # (If this folder is to be inside `PROBLEMS_DIR`, prepend an underscore so it is ignored by the problem importer.)
    PROBLEMS_STATIC_DIR = join(PROBLEMS_DIR, '_static')

    # Subfolder for problem static files
    PROBLEMS_STATIC_URL = 'ctfproblems'

    @classmethod
    def add_staticfiles_dir(cls):
        cls.STATICFILES_DIRS.append(
                (cls.PROBLEMS_STATIC_URL, cls.PROBLEMS_STATIC_DIR)
        )

    @classmethod
    def setup(cls):
        super().setup()
        cls.add_staticfiles_dir()


class Base(CTFlex, Gunicorn, Django):
    pass


class Dev(Base):
    # Security
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG  # TODO(Yatharth): Eliminate warning about TEMPLATE_* deprecation
    ALLOWED_HOSTS = ['*']


class Prod(Base):
    # Security
    DEBUG = False
    TEMPLATE_DEBUG = DEBUG
    SESSION_COOKIE_SECURE = True  # Only if HTTPS
    CSRF_COOKIE_SECURE = True  # Only if HTTPS
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # Only if nginx is properly configured
    ALLOWED_HOSTS = ['.pactf.com', '.pactf.cf']
