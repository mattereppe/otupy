"""File Collection Log Monitoring

This module collects all public definition that are exported as part of the fclm profile.
All naming follows as much as possible the terminology in the fclm Specification, by
also applying generic otupy conventions.

This definition also registers all extensions defined in the fclm profile (`Args`, `Target`, `Profile`, `Results`).

"""

from otupy.profiles.fclm.profile import Profile
from otupy.profiles.fclm.actuator import *

from otupy import TargetEnum
from otupy.profiles.fclm.data import *
from otupy.profiles.fclm.targets import LogMonitor
from otupy.profiles.fclm.targets import MonitorID

from otupy.profiles.fclm.data.collector import Collector
from otupy.profiles.fclm.data.file_format import FileFormat
from otupy.profiles.fclm.data.exporter import Exporter
from otupy.profiles.fclm.data.import_options import ImportOptions
from otupy.profiles.fclm.data.ef import EF
from otupy.profiles.fclm.data.socket import Socket

# According to the standard, extended targets must be prefixed with the nsid
from otupy.profiles.fclm.args import Args
from otupy.profiles.fclm.results import Results
from otupy.profiles.fclm.validation import (
    AllowedCommandTarget,
    AllowedCommandArguments,
    validate_command,
    validate_args,
)
