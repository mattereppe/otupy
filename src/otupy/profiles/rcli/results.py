"""RCLI Response extensions"""

import otupy as oc2

from otupy.profiles.rcli.profile import Profile
from otupy.profiles.rcli.targets import Processes, Files
from otupy.types.targets.file import File

# from otupy.profiles.rcli.data.extended_process import Process

from otupy.types.base.array_of import ArrayOf


@oc2.extension(nsid=Profile.nsid)
class Results(oc2.Results):
    """RCLI Results

    Extensions to the base class `otupy.core.response.Results`.

    [Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.

    """

    # fieldtypes = {'clicommands' : ArrayOf(Process)}
    # fieldtypes = dict(clicommands = ArrayOf(Process))

    fieldtypes = {"clicommands": Processes, "process_status": Processes, "file_status": Files}
