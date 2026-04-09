"""FCLM Response extensions"""

import otupy as oc2

from otupy.profiles.fclm.profile import Profile
from otupy.profiles.fclm.data.ef import EF
from otupy.profiles.fclm.targets.monitor_id import MonitorID

from otupy.types.base.array_of import ArrayOf


@oc2.extension(nsid=Profile.nsid)
class Results(oc2.Results):
    """FCLM Results

    Extensions to the base class `otupy.core.response.Results`.

    [Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.

    """

    fieldtypes = {
        "export_fields": ArrayOf(EF),
        "monitor_id": MonitorID,
        "exports_config": ArrayOf(str),
        "imports_config": ArrayOf(str),
        "import_controls": ArrayOf(str),
    }
