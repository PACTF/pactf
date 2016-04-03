"""Define common functionality and helpers for management commands"""

import sys

from IPython.core import ultratb
from django.core.management import CommandError

DEBUG_OPTION_NAME = 'debug'


# region Misc

def filter_dict(kwargs):
    """Return only the keys of a dictionary whose values are truthy"""
    return (key for key, value in kwargs.items() if value)


def debug_with_pdb(**options):
    """Debug errors interactively if debug option is true

    If the debug option is truthy, the Python exception handler will be set to
    give the user a PDB shell to examine the error (instead of to print the
    stacktrace and quit).
    """
    if options[DEBUG_OPTION_NAME]:
        sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=1)


# endregion


# region Management Command CLI Arguments

def add_no_input_argument(parser):
    parser.add_argument('--noinput', '--no-input', '-n',
                        action='store_false', dest='interactive', default=True,
                        help="Do NOT prompt the user for input of any kind.")


def add_debug_argument(parser):
    parser.add_argument('--debug', '-d',
                        action='store_true', dest=DEBUG_OPTION_NAME, default=False,
                        help="Launch a pdb session on encountering an exception.")


def add_clear_argument(parser):
    parser.add_argument('--clear', '-c',
                        action='store_true', dest='clear', default=False,
                        help="Clear existing content if it wasn't just updated.")

# endregion
