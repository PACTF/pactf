"""Import actual models and then connect signals"""

from ctflex.models.models import *
from ctflex import signals

signals.connect_signals()
