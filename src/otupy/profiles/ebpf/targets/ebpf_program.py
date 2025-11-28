
import otupy as oc2
from otupy.profiles.ebpf import profile
from otupy.types.base.array_of import ArrayOf
from otupy.types.base.record import Record
from otupy.profiles.ebpf.data.name import Name

@oc2.target(name="ebpf_program",nsid=None)
class ebpf_program(Record):
    """ Target che identifica un programma eBPF (file oggetto .o)
        da caricare o gestire nel kernel.
    """
    file_path:  ArrayOf(Name) = None # type: ignore
    prog_type:  ArrayOf(Name) = None # type: ignore

    def __init__(self, file_path = None, prog_type = None):
        self.file_path = ArrayOf(Name)(file_path) if file_path is not None else None
        self.prog_type = ArrayOf(Name)(prog_type) if prog_type is not None else None
    
    def __repr__(self):
            return (f"eBPF_Programs(files={self.file_path}, program_types={self.prog_type})")
    def __str__(self):
         return f"eBPF_Programs(" \
	            f"files={self.file_path}, " \
	            f"program_types={self.prog_type})"