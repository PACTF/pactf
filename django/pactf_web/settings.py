"""
Django settings for pactf_web project.

Generated using Django 1.8.6.
Quick-start development settings - unsuitable for production
See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/
"""

import os

from . import local_settings


# Directories

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The absolute path of the problems directory.
# FIXME: change this
PROBLEMS_DIR = os.path.join(BASE_DIR, '..', 'test_problems')


# Security

SECRET_KEY = '#051k601ed-6#vrbfow8tcjr=32fuffy-!nugv2k16%fv8&ipn'
DEBUG = True
ALLOWED_HOSTS = []


# Django App Config

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'markdown2',
    'ctf',
)

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


# Django Web config

ROOT_URLCONF = 'pactf_web.urls'

WSGI_APPLICATION = 'pactf_web.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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

# Static files
STATIC_URL = '/static/'


# Database

DATABASES = {
    'default': local_settings.TEST_DATABASE
}

# Make connections persistent
CONN_MAX_AGE = 60 * 60


# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
