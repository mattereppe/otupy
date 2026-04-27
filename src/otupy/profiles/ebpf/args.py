import otupy as oc2
from otupy.profiles.ebpf.profile import Profile
from otupy.types.base.array_of import ArrayOf
from otupy.types.base.record import Record
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.types.targets.file import File

@oc2.extension(nsid=Profile.nsid)
class Args(oc2.Args):
    """eBPF Args

    This class extends the Args defined in the Language Specification.
    The extension mechanism is described in the
    [Developing extensions](https://github.com/mattereppe/otupy/blob/main/docs/developingextensions.md#developing-extensions) Section of the main documentation.


    """

    fieldtypes = {"Direction": Direction, "AttachType": AttachType, "Interfaces": Interfaces, "maps":ArrayOf(str),"maps_required": bool}
