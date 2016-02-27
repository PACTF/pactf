"""Proxy all the settings CTFlex needs, providing defaults

The advantages of having this file are being able to:
- Refer to settings without the 'CTFLEX_' prefix
- Provide defaults while being DRY (which stands for "Don't Repeat Yourself")
- Look at all of the settings CTFlex uses at a glance
"""

from django.conf import settings


def get(key, default):
    return getattr(settings, key, default)


# TODO(Yatharth): Move more settings into here
SUPPORT_EMAIL = get('CTFLEX_SUPPORT_EMAIL', 'example@example.com')
CONTACT_EMAIL = get('CTFLEX_CONTACT_EMAIL', 'example@example.com')
SITENAME = get('CTFLEX_SITENAME', 'CTFlex')