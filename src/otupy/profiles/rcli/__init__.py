"""Remote CLI profile

This module collects all public definition that are exported as part of the RCLI profile.
All naming follows as much as possible the terminology in the RCLI Specification, by
also applying generic otupy conventions.

This definition also registers all extensions defined in the RCLI profile (`Args`, `Target`, `Profile`, `Results`).

"""

from otupy.profiles.rcli.profile import Profile
from otupy.profiles.rcli.actuator import *

from otupy import TargetEnum
from otupy.profiles.rcli.data import *
from otupy.profiles.rcli.targets import Processes
from otupy.profiles.rcli.targets import Files
from otupy.profiles.rcli.targets import Feature


# According to the standard, extended targets must be prefixed with the nsid
from otupy.profiles.rcli.args import Args
from otupy.profiles.rcli.results import Results
from otupy.profiles.rcli.validation import (
    AllowedCommandTarget,
    AllowedCommandArguments,
    validate_command,
    validate_args,
)
