"""Define constants for the project"""

from os.path import abspath, dirname, join

PROJECT_NAME = 'pactf'


ENVDIR_PATH = join(dirname(abspath(__file__)), 'envdir')
DJANGO_DIR = dirname(dirname(abspath(__file__)))
BASE_DIR = dirname(DJANGO_DIR)
