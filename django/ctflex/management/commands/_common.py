"""Extract common functionality and constants from management commands"""


def pass_through_argument(kwargs):
    """Return a tuple-unpackable iterable of only those argument keys whose value is truthy"""
    return (key for key, value in kwargs.items() if value)


def add_no_input(parser):
    parser.add_argument('--noinput', '--no-input', '-n',
                        action='store_false', dest='interactive', default=True,
                        help="Do NOT prompt the user for input of any kind.")


def add_debug(parser):
    parser.add_argument('--debug', '-d',
                        action='store_true', dest='debug', default=False,
                        help="Launch a pdb session on encountering an exception.")


def add_clear(parser):
    parser.add_argument('--clear', '-c',
                        action='store_true', dest='clear', default=False,
                        help="Clear existing content if it wasn't just updated.")
