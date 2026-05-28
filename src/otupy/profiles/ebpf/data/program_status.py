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

    Program: ProgramFile
    Direction: DirectionType
    hook_point: AttachType
    Interfaces: InterfacesType
    maps: ArrayOf(MapeBPF) # type: ignore[reportInvalidTypeForm]

    def __init__(self, Program=None, Direction=None, hook_point=None,
                 Interfaces=None, maps=None):
        super().__init__()
        self.Program = Program
        self.Direction = Direction
        self.hook_point = hook_point
        self.Interfaces = Interfaces
        self.maps = maps if maps is not None else ArrayOf(MapeBPF)()