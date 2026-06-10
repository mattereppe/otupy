""" eBPF Program Status """
from __future__ import annotations
from otupy.types.base.record import Record
from otupy.types.base.array_of import ArrayOf
from otupy.profiles.ebpf.data.map_ebpf import MapeBPF
from otupy.profiles.ebpf.data.direction_ebpf import Direction as DirectionType
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces as InterfacesType
from otupy.profiles.ebpf.data.source_file import ProgramFile


class ProgramStatus(Record):
    """
    OpenC2-compliant Record representing the runtime status of an eBPF program.
    Serialization/deserialization fully inherited from Record.
    """

    program: ProgramFile
    direction: DirectionType
    hook_point: AttachType
    interfaces: InterfacesType
    maps: ArrayOf(MapeBPF) # type: ignore[reportInvalidTypeForm]

    def __init__(self, program=None, direction=None, hook_point=None,
                 interfaces=None, maps=None):
        super().__init__()
        self.program = program
        self.direction = direction
        self.hook_point = hook_point
        self.interfaces = interfaces
        self.maps = maps if maps is not None else ArrayOf(MapeBPF)()