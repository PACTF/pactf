from os.path import join

from configurations import Configuration, values

from pactf.constants import BASE_DIR


# TODO(Yatharth): Prefix attributes and set django-configurations prefix appropriately

class Django:
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
        'django_countries',
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


class Security:

    SECRET_KEY = values.SecretValue()

    # Use PBKDF2PasswordHasher that uses 4 times the default number of iterations
    PASSWORD_HASHERS = ['ctflex.hashers.PBKDF2PasswordHasher4',
                        'django.contrib.auth.hashers.PBKDF2PasswordHasher']

    # Minimum password strength validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 12,
            }
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    # Number of days that a password reset link is valid for
    PASSWORD_RESET_TIMEOUT_DAYS = 1

    # Request modern browsers to block suspected XSS attacks. Not to be relied upon.
    SECURE_BROWSER_XSS_FILTER = True

    # Prevent browsers from guessing content types (reducing security risk).
    SECURE_CONTENT_TYPE_NOSNIFF = True


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


class Base(CTFlex, Gunicorn, Django, Security, Configuration):
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
    ALLOWED_HOSTS = ['.pactf.com', '.pactf.cf']

    https = True  # For settings that should only be true when using HTTPS
    SESSION_COOKIE_SECURE = https
    CSRF_COOKIE_SECURE = https

    # Only if nginx is properly configured
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

