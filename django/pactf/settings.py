"""Define (default) configuration for the project

This file uses django-configurations.
"""

import re
import socket
from os.path import join

from configurations import Configuration, values
from django.contrib import messages

import ctflex.constants
from pactf.constants import BASE_DIR


class _Django(Configuration):
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
        # 'email_log',
        'widget_tweaks',
        'django_print_settings',
        'post_office',
        'nocaptcha_recaptcha',

        # Django 3rd-party (local)
        # 'request',

        # Python 3rd-party
        'yaml',

        # Local
        # (pactf_web comes before ctflex to override the latter's templates.)
        'pactf_web',
        'ctflex',
    ]

    # (Order matters a lot here.)
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

        # Local
        # 'ctflex.middleware.RequestLoggingMiddleware',
        'ctflex.middleware.CloudflareRemoteAddrMiddleware',

        # Django Extensions
        'django.middleware.common.BrokenLinkEmailsMiddleware',

        # Django 3rd-party
        'ctflex.middleware.RatelimitMiddleware',
        # 'request.middleware.RequestMiddleware',

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
    LOGIN_REDIRECT_URL = 'ctflex:game'

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

    RATELIMIT_VIEW = values.Value('ctflex.views.ratelimited_view')

    # For Boostrap Alerts
    MESSAGE_TAGS = {
        messages.ERROR: 'danger'
    }
    STATICFILES_DIRS = values.ListValue([])

    # Admin URL
    ADMIN_URL_PATH = values.Value('admin')

    ''' Warnings '''

    WARNINGS_TO_SUPPRESS = values.ListValue([
        'RemovedInDjango110Warning: SubfieldBase has been deprecated. Use Field.from_db_value instead.',
        'RemovedInDjango110Warning: django.conf.urls.patterns() is deprecated and will be removed in Django 1.10. Update your urlpatterns to be a list of django.conf.urls.url() instances instead.'
    ])

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
            'LOCATION': '/var/run/memcached/memcached2.sock',
        }
    }

    @classmethod
    def suppress_warnings_to_suppress(cls):
        import logging
        warn_logger = logging.getLogger('py.warnings')
        warn_logger.addFilter(lambda record: not any(
            warning in record.getMessage() for warning in cls.WARNINGS_TO_SUPPRESS))

    # Setup
    @classmethod
    def post_setup(cls):
        cls.suppress_warnings_to_suppress()

    ''' Email '''

    email_prefix = 'EMAIL'

    EMAIL_HOST = values.Value('smtp.zoho.com', environ_prefix=None)
    EMAIL_PORT = values.IntegerValue(61539, environ_prefix=None)
    EMAIL_USE_TLS = values.BooleanValue(True, environ_prefix=None)

    EMAIL_HOST_USER = values.Value('noreply@pactf.com', environ_prefix=None)
    EMAIL_HOST_PASSWORD = values.SecretValue(environ_prefix=None)

    DEFAULT_FROM_EMAIL = values.Value(EMAIL_HOST_USER.value, environ_prefix=email_prefix)
    SERVER_EMAIL = values.Value(EMAIL_HOST_USER.value, environ_prefix=None)

    EMAIL_BACKEND = values.Value('post_office.EmailBackend', environ_prefix=None)
    EMAIL_CRON = values.BooleanValue(False, environ_prefix=None)

    EMAIL_RATELIMIT_NUMBER = values.IntegerValue(10, environ_prefix=None)
    EMAIL_RATELIMIT_SECONDS = values.IntegerValue(60, environ_prefix=None)

    @property
    def POST_OFFICE(self):
        return {
            'DEFAULT_PRIORITY': 'medium' if self.EMAIL_CRON else 'now',
            # 'BACKENDS': {
            #     'default': 'email_log.backends.EmailBackend',
            # },
        }

    ''' Logging '''

    CTFLEX_LOG_LEVEL = values.Value('INFO', environ_prefix=None)
    DJANGO_LOG_LEVEL = values.Value('WARNING', environ_prefix=None)

    @classmethod
    def set_logging(cls):
        cls.LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,

            'filters': {
                'require_debug_true': {
                    '()': 'django.utils.log.RequireDebugTrue',
                },
            },

            'formatters': {
                'detailed': {
                    'format': '%(levelname)-8s @ %(asctime)s in line:%(lineno)-4d of %(module)-17s : %(message)s'
                },
                'time': {
                    'format': '%(asctime)s %(message)s'
                }
            },

            'handlers': {
                # FIXME: rotating

                'request_file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': join(BASE_DIR, 'logs', 'request.log'),
                    'formatter': 'time',
                },
                'ctflex_file': {
                    'level': cls.CTFLEX_LOG_LEVEL,
                    'class': 'logging.FileHandler',
                    'filename': join(BASE_DIR, 'logs', 'ctflex.log'),
                    'formatter': 'detailed',
                },
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'detailed',
                },
                'mail_admins': {
                    'level': 'ERROR',
                    'class': 'pactf_web.loggers.ThrottledAdminEmailHandler',
                },
                'null': {
                    'class': 'logging.NullHandler',
                },
            },

            'loggers': {
                'django': {
                    'level': cls.DJANGO_LOG_LEVEL,
                    'handlers': ['console'],
                    'propagate': True,
                },
                'django.template': {
                    'level': 'WARNING',
                    'handlers': ['mail_admins', 'console'],
                    'propagate': True,
                },
                'django.request': {
                    'level': 'ERROR',
                    'handlers': ['mail_admins', 'console'],
                    'propagate': False,
                },
                ctflex.constants.BASE_LOGGER_NAME: {
                    'level': cls.CTFLEX_LOG_LEVEL,
                    'handlers': ['console', 'ctflex_file', 'mail_admins'],
                    'propagate': False,
                },
                ctflex.constants.IP_LOGGER_NAME: {
                    'level': 'INFO',
                    'handlers': ['request_file'],
                    'propogate': False,
                }
            },
        }

    @classmethod
    def setup(cls):
        super().setup()
        cls.set_logging()


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


class _Gunicorn:
    """Configure Gunicorn"""

    # As whom Gunicorn should run the server
    GUNICORN_USER = values.Value(environ_prefix=None)
    GUNICORN_GROUP = values.Value(environ_prefix=None)

    # Path to Gunicorn
    GUNICORN_PATH = values.PathValue('~/.virtualenvs/pactf/bin/gunicorn',
                                     environ_prefix=None, check_exists=False)

    # Whether to use a socket or serve directly to an address
    GUNICORN_USE_SOCKFILE = values.BooleanValue(False, environ_prefix=None)

    # Socket to communicate with
    GUNICORN_SOCKFILE = values.PathValue(join(BASE_DIR, 'run', 'gunicorn.sock'),
                                         environ_prefix=None, check_exists=False)

    # Url to directly serve to
    GUNICORN_IP = values.IPValue('127.0.0.1', environ_prefix=None)
    GUNICORN_PORT = values.IntegerValue(8001, environ_prefix=None)

    # Number of worker processes Gunicorn should spawn
    GUNICORN_NUM_WORKERS = values.IntegerValue(1, environ_prefix=None)


class _CTFlex(_Django, Configuration):
    """Configure CTFlex"""

    ''' General '''

    # CTFLEX_REGISTER_EMAIL = 'registrar@pactf.com'
    CTFLEX_SUPPORT_EMAIL = 'contact@pactf.com'
    CTFLEX_CONTACT_EMAIL = 'contact@pactf.com'

    CTFLEX_SITENAME = 'PACTF'

    # CTFLEX_ELIGIBILITY_FUNCTION = 'pactf_web.ctflex_helpers.eligible'

    CTFLEX_INCUBATING = values.BooleanValue(False, environ_prefix=None)
    CTFLEX_BOARD_CACHE_DURATION = values.IntegerValue(100, environ_prefix=None)

    ''' Problems and Staticfiles '''

    CTFLEX_PROBLEMS_DIR = values.Value(join(BASE_DIR, 'ctfproblems'), environ_prefix=None)
    CTFLEX_PROBLEMS_STATIC_DIR = values.Value(join(BASE_DIR, 'ctfproblems', '_static'), environ_prefix=None)
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

    ''' Convenience '''

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }


class Prod(_Base):
    """Secure and quiet settings for production"""

    ''' Security '''

    DEBUG = False
    ALLOWED_HOSTS = values.ListValue(['.pactf.com', '.pactf.cf'])

    https = values.Value(True)  # For settings that should only be true when using HTTPS
    SESSION_COOKIE_SECURE = https.value
    CSRF_COOKIE_SECURE = https.value

    https_headers = values.Value(True)  # Only enable this if nginx is properly configured with HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if https_headers else None

    NORECAPTCHA_SITE_KEY = values.Value('6Lf57x0TAAAAAH8qVHlGeuwLmf9vaDsdpnrJLSqA', environ_prefix=None)
    NORECAPTCHA_SECRET_KEY = values.SecretValue(environ_prefix=None)

    ''' Logging '''

    ADMINS = values.ListValue([
        ('Yatharth', 'yatharth999+pactf@gmail.com'),
        ('Tony', 'tony@tonytan.io'),
        # ('PACTF Errors', _Django.SERVER_EMAIL.value)
    ])

    IGNORABLE_404_URLS = values.ListValue([
        re.compile(r'^/apple-touch-icon.*\.png$'),
        re.compile(r'^/favicon\.ico$'),
        re.compile(r'^/robots\.txt$'),
    ])

    @staticmethod
    def get_hostname():
        try:
            return socket.gethostname()
        except:
            return None

    @classmethod
    def set_email_subject_prefix(cls):
        hostname = cls.get_hostname()
        if hostname:
            cls.EMAIL_SUBJECT_PREFIX = "[Django {}] ".format(hostname)

    ''' General '''

    @classmethod
    def pre_setup(cls):
        super().setup()
        cls.set_email_subject_prefix()


class FakeProd(Prod):
    """Fake Prod during development"""

    ''' Security '''

    NORECAPTCHA_SITE_KEY = values.Value('6LeF8h0TAAAAAMJrdcK8g7nn1lGVCNbgzskXHj5S', environ_prefix=None)
    NORECAPTCHA_SECRET_KEY = values.Value('6LeF8h0TAAAAAP_U_TIChL_6y8cTiu2jhTg1cdzG', environ_prefix=None)

    ''' Logging '''

    ADMINS = values.ListValue([
        ('Yatharth', 'yatharth999+pactf@gmail.com'),
    ])

    ''' Convenience '''

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

    TEMPLATE_STRING_IF_INVALID = 'DEBUG WARNING: undefined template variable [%s] not found'
