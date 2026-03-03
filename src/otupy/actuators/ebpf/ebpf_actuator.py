import logging
from otupy import Version, StatusCode
from otupy import  StatusCodeDescription, Actions, Command, Response
from otupy.actuators.ebpf.programs.TCprogram import TCProgram
from otupy.actuators.ebpf.managers.ebpf_program_manager import EBPFProgramManager
from otupy.core.actuator import actuator_implementation
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.query_results import QueryResults
from otupy.types.base.array_of import ArrayOf
from otupy.actuators.ebpf.programs.XDPprogram import XDPProgram


@actuator_implementation("x-ebpf")
class eBPFActuator:
    def __init__(self,  **kwargs):

        self.auth = kwargs['auth'] if 'auth' in kwargs else None
        self.config = kwargs['config'] if 'config' in kwargs else None
        self.peers = kwargs['peers'] if 'peers' in kwargs else None
        self.owner = kwargs['owner'] if 'owner' in kwargs else None
        self.specifiers = kwargs['specifiers'] if 'specifiers' in kwargs else None
        self.manager = EBPFProgramManager()
        self.manager.register_program_type("tc", TCProgram)
        self.manager.register_program_type("xdp", XDPProgram)
        self.logger = logging.getLogger(__name__)

    def run(self, cmd: Command) -> Response:
        try:

            match cmd.action:
                case Actions.create: return self.create(cmd)
                case Actions.query: return self.query(cmd)
                case Actions.delete: return self.delete(cmd)
                case _: return self.__notimplemented(cmd)
        except Exception as e:
            return self.__servererror(cmd, e)

    def create(self, cmd: Command) -> Response:
        obj = cmd.target.getObj()
        if obj.file is None or obj.direction is None or obj.attach_type is None:
            return Response(StatusCode.BAD_REQUEST, "Missing required eBPF parameters")

        try:
            prog_type = obj.attach_type.Name.lower()
            prog = self.manager.create_program(
                prog_type,
                prog_path=obj.file.Name,
                section=obj.file.Section,
                direction=obj.direction.Name.lower()
            )
            prog.load(ifaces=["wlp7s0"])
            return Response(StatusCode.OK, "Program loaded successfully")
        except Exception as e:
            self.logger.exception(e)
            return Response(StatusCode.INTERNAL_ERROR, f"Failed to attach eBPF program: {type(e)}")

    def query(self, cmd: Command) -> Response:
        target = cmd.target.getObj()
        try:
            prog_type = target.attach_type.Name.lower() if target.attach_type else None
            if prog_type:
                programs = self.manager.create_program(prog_type, prog_path=target.file.Name).query()
            else:
                programs = []
                for name in self.manager.registered_programs:
                    programs.extend(self.manager.create_program(name, prog_path=target.file.Name).query())

            program_files = [ProgramFile(Program=p["program"], Section=p.get("section")) for p in programs]
            results = QueryResults(
                Program=ArrayOf(ProgramFile)(program_files),
                hook_point=ArrayOf(AttachType)([p["attach_type"] for p in programs]),
                Direction=ArrayOf(Direction)([p["direction"] for p in programs]),
                Interfaces=ArrayOf(Interfaces)([p["interface"] for p in programs])
            )
            return Response(StatusCode.OK, f"{len(programs)} programs loaded", results)
        except Exception as e:
            self.logger.exception(e)
            return Response(StatusCode.INTERNAL_ERROR, f"Failed to retrieve eBPF programs: {type(e)}")

    def delete(self, cmd: Command) -> Response:
        target = cmd.target.getObj()
        try:
            prog_type = target.attach_type.Name.lower() if target.attach_type else None
            prog = self.manager.create_program(
                prog_type,
                prog_path=target.file.Name,
                section=target.file.Section,
                direction=target.direction.Name.lower()
            )
            prog.remove(ifaces=target.interfaces.Names if target.interfaces else None)
            Response(status=StatusCode.OK, status_text="TODO REMOVE EBPF ACTUATOR")
        except Exception as e:
            self.logger.exception(e)
            return Response(StatusCode.INTERNAL_ERROR, f"Failed to remove eBPF program: {type(e)}")

    def __notimplemented(self, cmd: Command):
        return Response(StatusCode.NOTIMPLEMENTED, f'Action {cmd.action.name} not implemented')

    def __servererror(self, cmd: Command, e: Exception):
        self.logger.exception(e)
        return Response(StatusCode.INTERNAL_ERROR, 'Internal server error')