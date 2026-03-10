

import otupy as oc2
from otupy.types.base.record import Record
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType

@oc2.target(name="eBPF_load_TCprogram", nsid=None)
class eBPF_load_TCprogram(Record):
    """
    OpenC2-compliant target record for loading an eBPF program file.
    """

    # ------------------------
    # OpenC2 public fields
    # ------------------------
    file: ProgramFile = None
    direction: Direction = None
    attach_type: AttachType = None
    interface: str = None

    def __init__(self, file: ProgramFile = None, direction: Direction = None, attach_type: AttachType = None, interface: str = None):
        super().__init__()

        # Assign directly to public fields for OpenC2 serialization
        self.file = file
        self.direction = direction
        self.attach_type = attach_type
        self.interface = interface

    # ------------------------
    # Representation
    # ------------------------
    def __repr__(self):
        return f"eBPF_Programs(file={self.file}, interface={self.interface}, hook={self.attach_type}, direction={self.direction})"

    def __str__(self):
        return f"eBPF_Programs(file={self.file}, interface={self.interface},hook={self.attach_type}, direction={self.direction})"

    # ------------------------
    # Serialization for OpenC2 JSON
    # ------------------------
    def to_dict(self):
        return {
            "file": self.file.to_dict() if self.file else None,
            "file": self.interface.to_dict() if self.interface else None,
            "direction": self.direction.to_dict() if self.direction else None,
            "attach_type": self.attach_type.to_dict() if self.attach_type else None
        }
