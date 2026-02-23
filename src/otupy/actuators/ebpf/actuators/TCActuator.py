import logging
from otupy import Version, StatusCode
from otupy import  StatusCodeDescription, Actions, Command, Response
from otupy.actuators.ebpf.base.base_ebpf_actuator import BaseEBPFActuator
from otupy.actuators.ebpf.programs.TCprogram import TCProgram
from otupy.actuators.ebpf.managers.ebpf_program_manager import EBPFProgramManager
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.query_results import QueryResults
from otupy.types.base.array_of import ArrayOf
from otupy.actuators.ebpf.programs.XDPprogram import XDPProgram

class TCActuator(BaseEBPFActuator):
    def __init__(self, manager):
        self.manager = manager
        self.logger = logging.getLogger(__name__)

    def create(self, cmd: Command) -> Response:
        obj = cmd.target.getObj()
        prog = self.manager.create_program("tc", prog_path=obj.file.Name, section=obj.file.Section, direction=obj.direction.Name.lower())
        prog.load(ifaces=obj.interfaces.Names if obj.interfaces else None)
        return Response(StatusCode.OK, "TC program loaded successfully")

    def query(self, cmd: Command) -> Response:
        pass
    def delete(self, cmd: Command) -> Response:
        obj = cmd.target.getObj()
        prog = self.manager.create_program("tc", prog_path=obj.file.Name, section=obj.file.Section, direction=obj.direction.Name.lower())
        prog.remove(ifaces=obj.interfaces.Names if obj.interfaces else None)
        return Response(StatusCode.OK, "TC program removed successfully")