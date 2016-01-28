from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2PasswordHasher4(PBKDF2PasswordHasher):
    """
    A subclass of PBKDF2PasswordHasher that uses 4 times the default number of iterations.
    """
    iterations = PBKDF2PasswordHasher.iterations * 4
