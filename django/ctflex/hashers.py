"""Define hashing functions and classes"""

import zlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher

from ctflex import settings


class PBKDF2PasswordHasher4(PBKDF2PasswordHasher):
    """Use 4 times the default number of iterations """
    iterations = PBKDF2PasswordHasher.iterations * 4


def dyanamic_problem_key(team):
    """Compute hash for passing to dynamic problem generators and graders

    adler32 is not very secure, but that’s okay.
    """
    data = str(team.id) + settings.PROBLEM_SALT + settings.SECRET_KEY
    return zlib.adler32(bytes(data, 'utf-8'))
