import otupy as oc2
from otupy.profiles.ebpf.profile import Profile
from otupy.types.base.record import Record
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces

@oc2.target(name="eBPF_program", nsid=Profile.nsid)
class eBPF_program(Record):
    """
    OpenC2-compliant target record for loading an eBPF program file.
    """

    # ------------------------
    # OpenC2 public fields
    # ------------------------
    file: ProgramFile = None
    def __init__(self, file: ProgramFile = None):
        super().__init__()

        
        self.file = file

    # ------------------------
    # Representation
    # ------------------------
    def __repr__(self):
        return f"eBPF_Programs(file={self.file})"

    def __str__(self):
        return f"eBPF_Programs(file={self.file})"

    # ------------------------
    # Serialization for OpenC2 JSON
    # ------------------------
    def to_dict(self):
        return {
            "file": self.file.to_dict() if self.file else None
        }
