"""Hold app-specific constants

These constants can't just be stored in `models.py` because `apps.py` can't import `models.py`.
"""

import re


# COMPETE_PERMISSION_CODENAME = 'compete'
# COMPETITOR_GROUP_NAME = 'ctf.competitors'

UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
