from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2PasswordHasher4(PBKDF2PasswordHasher):
    """Subclass PBKDF2PasswordHasher to use 4 times the default number of iterations
    """
    iterations = PBKDF2PasswordHasher.iterations * 4
