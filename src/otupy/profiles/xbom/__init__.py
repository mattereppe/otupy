""" XBOM profile

	This module collects all public definition that are exported as part of the XBOM profile.
	All naming follows as much as possible the terminology in the XBOM Specification, by
	also applying generic otupy conventions.

	This definition also registers all extensions defined in the XBOM profile (`Args`, `Target`, `Profile`, `Results`).

"""

from otupy.profiles.xbom.profile import Profile
from otupy.profiles.xbom.actuator import *

from otupy import TargetEnum
from otupy.profiles.xbom.data import *
from otupy.profiles.xbom.data.sbom_format import SbomFormat
from otupy.profiles.xbom.targets import Context, SbomCtx


# According to the standard, extended targets must be prefixed with the nsid
from otupy.profiles.xbom.args import Args
from otupy.profiles.xbom.results import Results
from otupy.profiles.xbom.validation import AllowedCommandTarget, AllowedCommandArguments, validate_command, validate_args
