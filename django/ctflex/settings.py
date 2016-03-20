"""Proxy all the settings CTFlex needs, providing defaults

This file enables:
- Referring to settings without the 'CTFLEX_' prefix
- Providing defaults while being DRY (which stands for "Don't Repeat Yourself")
- Looking at all of the settings CTFlex uses at a glance
"""

from django.conf import settings

_PREFIX = 'CTFLEX_'
_SETTINGS = (

    ### General

    ('AUTH_USER_MODEL', None, 'AUTH_USER_MODEL'),

    ('SECRET_KEY', None, 'SECRET_KEY'),

    # How many competitors can be in one team
    ('MAX_TEAM_SIZE', 5, None),

    # # Function taking a team as its sole argument and returning whether it is
    # # eligible for prizes and being ranked
    # ('ELIGIBILITY_FUNCTION', '', None),

    # Whether the incubating middleware is enabled
    ('INCUBATING', False, None),

    ### Metadata

    # Name used for site in emails sent out
    ('SITENAME', 'CTFlex', None),

    ('REGISTER_EMAIL', 'example@example.com', None),
    ('SUPPORT_EMAIL', 'example@example.com', None),
    ('CONTACT_EMAIL', 'example@example.com', None),

    ### URLs and Views

    ('OVERALL_WINDOW_CODENAME', 'overall', None),

    ('LOGIN_REDIRECT_URL', 'ctflex:index', 'LOGIN_REDIRECT_URL'),
    ('WINDOW_CHANGE_URL', 'ctflex:game', None),
    ('LOGOUT_REDIRECT_URL', 'ctflex:index', None),
    ('TEAM_CHANGE_REDIRECT_URL', 'ctflex:current_team', None),
    ('INVALID_STATE_REDIRECT_URL', 'ctflex:index', None),

    ### Problems

    # A salt prepended to SECRET_KEY while non-securely hashing for dynamic problems
    ('PROBLEM_SALT', 'CsffrLAU', None),

    # Directory containing problem folders
    ('PROBLEMS_DIR', None, None),

    # Extras for the markdown2 Python module for formatting problem description and hints
    # TODO: Download 2.3.1 of markdown2 to get spoiler goodiness
    ('MARKDOWN_EXTRAS', ('fenced-code-blocks', 'smarty-pants', 'spoiler', 'strike'), None),

    ### Static

    # Intermediate folder for storing problem static files
    # (`manage.py loadprobs` will collect files to here, and `manage.py collectstatic`
    #  will collect from here to static.)
    # (If this folder is to be inside `PROBLEMS_DIR`, prepend an underscore so it is
    #  ignored by the problem importer.)
    ('PROBLEMS_STATIC_DIR', None, None),

    # URL to serve problem static files at
    ('PROBLEMS_STATIC_URL', None, None),

)

for local_name, default, settings_name in _SETTINGS:

    # Default to prefixing setting names
    if settings_name is None:
        settings_name = _PREFIX + local_name

    # Get setting, defaulting if appropriate
    value = getattr(settings, settings_name, default)

    # Set setting on this module
    globals()[local_name] = value
