from . import version

# Checking version
__version__ = version.__version__

import sys
import os

if sys.version_info.major < 3:
  import warnings
  warnings.warn("Only supports python3!")

# Loading all the various methods
#from . import analysis
from . import cli
from . import tbc
#from . import gui

