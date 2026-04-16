"""Netflow Monitor

This module collects all public definition that are exported as part of the NFM profile.
All naming follows as much as possible the terminology in the NFM Specification, by
also applying generic openc2lib conventions.

This definition also registers all extensions defined in the NFM profile (`Args`, `Target`, `Profile`, `Results`).

"""

from otupy.profiles.nfm.profile import Profile
from otupy.profiles.nfm.actuator import *

from otupy import TargetEnum
from otupy.profiles.nfm.data import *
from otupy.profiles.nfm.targets import FlowMonitor
from otupy.profiles.nfm.targets import MonitorID


# According to the standard, extended targets must be prefixed with the nsid
from otupy.profiles.nfm.args import Args
from otupy.profiles.nfm.results import Results
from otupy.profiles.nfm.validation import (
    AllowedCommandTarget,
    AllowedCommandArguments,
    validate_command,
    validate_args,
)
