"""RCLI Arguments

This module extends the Args defined by the Language Specification
(see Sec. 'Command Arguments Unique to RCLI').
"""

import otupy as oc2

from otupy.profiles.rcli.profile import Profile
from otupy import TargetEnum
from otupy.types.targets.file import File


@oc2.extension(nsid=Profile.nsid)
class Args(oc2.Args):
    """RCLI Args

    This class extends the Args defined in the Language Specification.
    The extension mechanism is described in the
    [Developing extensions](https://github.com/mattereppe/openc2lib/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.


    """

    # fieldtypes = {'storage': oc2.File}
    fieldtypes = {"storage": File}
