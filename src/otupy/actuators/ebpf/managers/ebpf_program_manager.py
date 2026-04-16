from typing import Type, Dict

from otupy.actuators.ebpf.base.ebpf_base import BaseEBPFProgram

class EBPFProgramManager:
    """
    Manages multiple eBPF program types.
    """

    def __init__(self):
        self.registered_programs: Dict[str, Type[BaseEBPFProgram]] = {}

    def register_program_type(self, name: str, program_cls: Type[BaseEBPFProgram]):
        """Register a new eBPF program type"""
        self.registered_programs[name] = program_cls

    def create_program(self, name: str, *args, **kwargs) -> BaseEBPFProgram:
        """Instantiate a program by type."""
        cls = self.registered_programs.get(name)
        if not cls:
            raise ValueError(f"Program type '{name}' not registered")
        return cls(*args, **kwargs)