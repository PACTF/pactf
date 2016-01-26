"""
Django settings for pactf_web project.

Generated using Django 1.8.6.
Quick-start development settings - unsuitable for production
See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/
"""

from os.path import abspath, dirname, join


# Django App Config

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

    # 3rd-party Django
    'django_extensions',
    'debug_toolbar',

    # 3rd-party Python
    'yaml',

    # Ours
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


# Django Web config

ROOT_URLCONF = 'pactf_web.urls'

WSGI_APPLICATION = 'pactf_web.wsgi.application'

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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Local config

# (This import comes in last because local settings should have priority.)
from pactf_web.local_settings import *
