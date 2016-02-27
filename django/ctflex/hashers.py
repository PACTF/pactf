"""Define hashing functions and classes"""

import zlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.conf import settings

from ctflex import constants


class PBKDF2PasswordHasher4(PBKDF2PasswordHasher):
    """Subclass PBKDF2PasswordHasher to use 4 times the default number of iterations
    """
    iterations = PBKDF2PasswordHasher.iterations * 4


def dyanamic_problem_key(team):
    return zlib.adler32(bytes(str(team.id) + constants.PROBLEM_SALT + settings.SECRET_KEY, 'utf-8'))
