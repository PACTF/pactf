"""Define (default) configuration for the project

This file uses django-configurations.
"""

import os
import re
from os.path import join

from configurations import Configuration, values
from django.contrib import messages

import ctflex.constants
from pactf.constants import BASE_DIR


class _Django:
    """Configure basic Django things"""

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
        'django.contrib.humanize',

        # Django 3rd-party
        'django_countries',
        'django_extensions',
        'debug_toolbar',
        'email_log',
        'widget_tweaks',

        # Python 3rd-party
        'yaml',

        # Local
        # (pactf_web comes before ctflex to override the latter's templates.)
        'pactf_web',
        'ctflex',
    ]

    MIDDLEWARE_CLASSES = (
        # Django Defaults
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.middleware.security.SecurityMiddleware',

        # Django Extensions
        'django.middleware.common.BrokenLinkEmailsMiddleware',

        # Django 3rd-party
        'ctflex.middleware.RatelimitMiddleware',

        # Local
        'ctflex.middleware.IncubatingMiddleware',
    )

    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )

    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    # Default
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',

                    # CTFlex
                    'ctflex.views.default_context'
                ],
            },
        },
    ]

    ROOT_URLCONF = 'pactf.urls'

    WSGI_APPLICATION = 'pactf.wsgi.application'

    # URL to serve static files at
    STATIC_URL = '/static/'

    # Make connections persistent
    CONN_MAX_AGE = 60 * 60

    # Auth URLs
    LOGIN_URL = 'ctflex:login'
    LOGOUT_URL = 'ctflex:logout'
    LOGIN_REDIRECT_URL = 'ctflex:index'

    # Internationalization
    LANGUAGE_CODE = 'en-us'
    TIME_ZONE = 'America/New_York'
    USE_I18N = True
    USE_L10N = True
    USE_TZ = True

    # Database
    # (Postgres is required for CTFlex's CtfProblem's JSONField.)
    DATABASES = values.DatabaseURLValue(environ_required=True)

    # Where to finally collect static files to
    # (Point your server (nginx, Apache etc.) to serve from this folder directly.)
    STATIC_ROOT = join(BASE_DIR, 'static')

    RATELIMIT_VIEW = values.Value('ctflex.views.ratelimited')

    # For Boostrap Alerts
    MESSAGE_TAGS = {
        messages.ERROR: 'danger'
    }
    STATICFILES_DIRS = values.ListValue([])

    ''' Email '''

    email_prefix = 'EMAIL'

    EMAIL_HOST = values.Value('smtp.zoho.com', environ_prefix=None)
    EMAIL_PORT = values.IntegerValue(587, environ_prefix=None)
    EMAIL_USE_TLS = values.BooleanValue(True, environ_prefix=None)

    EMAIL_HOST_USER = values.Value('noreply@pactf.com', environ_prefix=None)
    EMAIL_HOST_PASSWORD = values.SecretValue(environ_prefix=None)

    DEFAULT_FROM_EMAIL = values.Value(EMAIL_HOST_USER.value, environ_prefix=email_prefix)
    SERVER_EMAIL = values.Value(EMAIL_HOST_USER.value, environ_prefix=None)

    EMAIL_BACKEND = values.Value('email_log.backends.EmailBackend', environ_prefix=None)


class _Security:
    """Configure security"""

    SECRET_KEY = values.SecretValue()

    # Use PBKDF2PasswordHasher that uses 4 times the default number of iterations
    PASSWORD_HASHERS = ['ctflex.hashers.PBKDF2PasswordHasher4',
                        'django.contrib.auth.hashers.PBKDF2PasswordHasher']

    # Number of days that a password reset link is valid for
    PASSWORD_RESET_TIMEOUT_DAYS = 1

    # Request modern browsers to block suspected XSS attacks. Not to be relied upon.
    SECURE_BROWSER_XSS_FILTER = True

    # Prevent browsers from guessing content types (reducing security risk).
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Minimum password strength validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 10,
            }
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    ''' Logging '''

    ADMINS = values.ListValue([
        ('Yatharth', 'yatharth999+pactf@gmail.com'),
        ('Tony', 'tony@tonytan.io'),
    ])
    MANAGERS = ADMINS.value

    IGNORABLE_404_URLS = values.ListValue([
        re.compile(r'^/apple-touch-icon.*\.png$'),
        re.compile(r'^/favicon\.ico$'),
        re.compile(r'^/robots\.txt$'),
    ])


class _Gunicorn:
    """Configure Gunicorn"""

    # As whom Gunicorn should run the server
    GUNICORN_USER = values.Value(environ_prefix=None)
    GUNICORN_GROUP = values.Value(environ_prefix=None)

    # Path to Gunicorn
    GUNICORN_PATH = values.PathValue('~/.virtualenvs/pactf/bin/gunicorn', environ_prefix=None)

    # Whether to use a socket or serve directly to an address
    GUNICORN_USE_SOCKFILE = values.BooleanValue(False, environ_prefix=None)

    # Socket to communicate with
    GUNICORN_SOCKFILE = values.PathValue(join(BASE_DIR, 'run', 'gunicorn.sock'),
                                         check_exists=False, environ_prefix=None)

    # Url to directly serve to
    GUNICORN_IP = values.IPValue('127.0.0.1', environ_prefix=None)
    GUNICORN_PORT = values.IntegerValue(8001, environ_prefix=None)

    # Number of worker processes Gunicorn should spawn
    GUNICORN_NUM_WORKERS = values.IntegerValue(3, environ_prefix=None)


class _CTFlex(_Django, Configuration):
    """Configure CTFlex"""

    ''' General '''

    CTFLEX_SUPPORT_EMAIL = 'support@pactf.com'
    CTFLEX_CONTACT_EMAIL = 'contact@pactf.com'

    CTFLEX_SITENAME = 'PACTF'

    # CTFLEX_ELIGIBILITY_FUNCTION = 'pactf_web.ctflex_helpers.eligible'

    CTFLEX_INCUBATING = values.BooleanValue(False, environ_prefix=None)

    ''' Problems and Staticfiles '''

    CTFLEX_PROBLEMS_DIR = values.Value(join(BASE_DIR, 'ctfproblems'), environ_prefix=None)
    CTFLEX_PROBLEMS_STATIC_DIR = join(CTFLEX_PROBLEMS_DIR.value, '_static')
    CTFLEX_PROBLEMS_STATIC_URL = 'ctfproblems'

    @classmethod
    def add_staticfiles_dir(cls):
        cls.STATICFILES_DIRS.append(
            (cls.CTFLEX_PROBLEMS_STATIC_URL, cls.CTFLEX_PROBLEMS_STATIC_DIR)
        )

    ''' General '''

    @classmethod
    def setup(cls):
        super().setup()
        cls.add_staticfiles_dir()


# TODO(Yatharth): Figure out why putting CTFlex before Security screws up SECRET_KEY
class _Base(_Security, _CTFlex, _Gunicorn, _Django, Configuration):
    """Extract common sub-classes of any full user-facing settings class"""
    pass


class Dev(_Base):
    """Insecure and noisy settings for development"""

    ''' Security '''

    DEBUG = True
    ALLOWED_HOSTS = values.ListValue(['*'])
    RATELIMIT_ENABLE = values.Value(False)
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 2,
            }
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    ''' Logging '''

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            # 'file': {
            #     'level': 'DEBUG',
            #     'class': 'logging.FileHandler',
            #     'filename': join(BASE_DIR, 'logs', 'django.log'),
            # },
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
                'propagate': True,
            },
            ctflex.constants.LOGGER_NAME: {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }


class Prod(_Base):
    """Secure and quite settings for production"""

    ''' Security '''

    DEBUG = False
    ALLOWED_HOSTS = values.ListValue(['.pactf.com', '.pactf.cf'])

    https = values.Value(True)  # For settings that should only be true when using HTTPS
    SESSION_COOKIE_SECURE = https.value
    CSRF_COOKIE_SECURE = https.value

    https_headers = values.Value(True)  # Only enable this if nginx is properly configured with HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if https_headers else None
