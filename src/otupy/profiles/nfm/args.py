"""NFM Arguments

This module extends the Args defined by the Language Specification
(see Sec. 'Command Arguments Unique to NFM').
"""

import otupy as oc2

from otupy.profiles.nfm.profile import Profile
from otupy.profiles.nfm.data.exporter import Exporter
from otupy.profiles.nfm.data.export_options import ExportOptions


@oc2.extension(nsid=Profile.nsid)
class Args(oc2.Args):
    """NFM Args

    This class extends the Args defined in the Language Specification.
    The extension mechanism is described in the
    [Developing extensions](https://github.com/mattereppe/openc2lib/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.


    """

    fieldtypes = {"exporter": Exporter, "exporter_options": ExportOptions}
