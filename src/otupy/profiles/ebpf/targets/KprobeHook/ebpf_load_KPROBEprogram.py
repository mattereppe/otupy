import otupy as oc2
from otupy.types.base.record import Record
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.kernel_function import KernelFunction  

@oc2.target(name="eBPF_load_KprobeProgram", nsid=None)
class eBPF_load_KprobeProgram(Record):
    """
    OpenC2-compliant target record for loading a kprobe eBPF program.
    """

    # ------------------------
    # OpenC2 public fields
    # ------------------------
    file: ProgramFile = None
    function: KernelFunction = None
    attach_type: AttachType = None   

    def __init__(
        self,
        file: ProgramFile = None,
        function: KernelFunction = None,
        attach_type: AttachType = None,
    ):
        super().__init__()

        self.file = file
        self.function = function
        self.attach_type = attach_type

    # ------------------------
    # Representation
    # ------------------------
    def __repr__(self):
        return (
            f"eBPF_Kprobe(file={self.file}, "
            f"function={self.function}, "
            f"hook={self.attach_type})"
        )

    def __str__(self):
        return (
            f"eBPF_Kprobe(file={self.file}, "
            f"function={self.function}, "
            f"hook={self.attach_type})"
        )

    # ------------------------
    # Serialization for OpenC2 JSON
    # ------------------------
    def to_dict(self):
        return {
            "file": self.file.to_dict() if self.file else None,
            "function": self.function.to_dict() if self.function else None,
            "attach_type": self.attach_type.to_dict() if self.attach_type else None,
        }