#!/usr/bin/env python

"""Execute management commands"""

import sys

import envdir

from pactf.constants import ENVDIR_PATH

if __name__ == "__main__":
    envdir.open(ENVDIR_PATH)

    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)
