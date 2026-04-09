"""FCLM Arguments

This module extends the Args defined by the Language Specification
(see Sec. 'Command Arguments Unique to FCLM').
"""

import otupy as oc2

from otupy.profiles.fclm.profile import Profile
from otupy import TargetEnum
from otupy.profiles.fclm.data.exporter import Exporter
from otupy.profiles.fclm.data.import_options import ImportOptions
from otupy.profiles.fclm.data.ef import EF


@oc2.extension(nsid=Profile.nsid)
class Args(oc2.Args):
    """FCLM Args

    This class extends the Args defined in the Language Specification.
    The extension mechanism is described in the
    [Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.


    """

    fieldtypes = {"log_exporter": Exporter, "export_fields": oc2.ArrayOf(EF), "import_controls": ImportOptions}
