"""NFM Response extensions"""

import otupy as oc2

from otupy.profiles.nfm.profile import Profile
from otupy.profiles.nfm.data.ie import IE
from otupy.profiles.nfm.data.interface import Interface
from otupy.profiles.nfm.targets.monitor_id import MonitorID

from otupy.types.base.array_of import ArrayOf


@oc2.extension(nsid=Profile.nsid)
class Results(oc2.Results):
    """NFM Results

    Extensions to the base class `openc2lib.core.response.Results`.

    [Developing extensions](https://github.com/mattereppe/openc2lib/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.

    """

    fieldtypes = {
        "interfaces": ArrayOf(Interface),
        "information_elements": ArrayOf(IE),
        "monitor_id": MonitorID,
        "exports": ArrayOf(str),
        "export_options": ArrayOf(str),
        "flow_format": ArrayOf(str),
        "filters": ArrayOf(str),
    }
