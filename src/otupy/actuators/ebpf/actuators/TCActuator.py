import logging
from otupy import Version, StatusCode
from otupy import   Actions, Command, Response
from otupy.actuators.ebpf.base.base_ebpf_actuator import BaseEBPFActuator
from otupy.actuators.ebpf.programs.TCprogram import TCProgram
from otupy.actuators.ebpf.managers.ebpf_program_manager import EBPFProgramManager
from otupy.core.actuator import actuator_implementation
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.query_results import QueryResults
from otupy.types.base.array_of import ArrayOf
from otupy.profiles.ebpf.validation.TCHookValidation import validate_command


from otupy.profiles.ebpf.targets.TCHook.eBPF_load_TCprogram import eBPF_load_TCprogram
from otupy.profiles.ebpf.targets.TCHook.eBPF_remove_TCprogram import eBPF_remove_TCprogram
from otupy.profiles.ebpf.targets.TCHook.eBPF_query_TCProgram import eBPF_query_TCProgram

@actuator_implementation("x-TCebpf")
class TCActuator(BaseEBPFActuator):
    def __init__(self,  **kwargs):

        self.auth = kwargs['auth'] if 'auth' in kwargs else None
        self.config = kwargs['config'] if 'config' in kwargs else None
        self.peers = kwargs['peers'] if 'peers' in kwargs else None
        self.owner = kwargs['owner'] if 'owner' in kwargs else None
        self.specifiers = kwargs['specifiers'] if 'specifiers' in kwargs else None
        self.manager = EBPFProgramManager()
        self.manager.register_program_type("tc", TCProgram)
        self.logger = logging.getLogger(__name__)

    def run(self, cmd: Command) -> Response:
        if not validate_command(cmd):
            return Response(status=StatusCode.NOTIMPLEMENTED, status_text='Invalid Action/Target pair')
        match cmd.action:
            case Actions.create: return self.create(cmd)
            case Actions.query: return self.query(cmd)
            case Actions.delete: return self.delete(cmd)
            case _: return self.__notimplemented(cmd)


    def create(self, cmd: Command) -> Response:
        obj : eBPF_load_TCprogram  = cmd.target.getObj()
        if obj.file is None or obj.direction is None or obj.attach_type is None or obj.interface:
            return Response(status=StatusCode.BAD_REQUEST, status_text="Missing required eBPF parameters")

        try:
            prog_type = obj.attach_type.Name.lower()
            prog = self.manager.create_program(
                prog_type,
                prog_path=obj.file.Name,
                section=obj.file.Section,
                direction=obj.direction.Name.lower()
            )
            prog.load(ifaces=obj.interface)
            return Response(status=StatusCode.OK, status_text="Program loaded successfully")
        except Exception as e:
            self.logger.exception(e)
            return self.__servererror(cmd, e)

    def query(self, cmd: Command) -> Response:
        target : eBPF_query_TCProgram= cmd.target.getObj()
        try:
            prog_type = target.attach_type.Name.lower() if target.attach_type else None
            programs = self.manager.create_program(prog_type).query(attach_type = prog_type)
           

            program_files = [ProgramFile(Program=p["file"], Section=p.get("section")) for p in programs]
            results = QueryResults(
                Program=ArrayOf(ProgramFile)(program_files),
                hook_point=ArrayOf(AttachType)([p["attach_type"] for p in programs]),
                Direction=ArrayOf(Direction)([p["direction"] for p in programs]),
                Interfaces=ArrayOf(Interfaces)([p["interface"] for p in programs])
            )
            return Response(status=StatusCode.OK, status_text=f"{len(programs)} programs loaded", results=results)
        except Exception as e:
            self.logger.exception(e)
            return self.__servererror(cmd, e)

    def delete(self, cmd: Command) -> Response:
        target : eBPF_remove_TCprogram= cmd.target.getObj()
        if target.file is None or target.direction is None or target.attach_type is None or target.interfaces is None:
            return Response(status=StatusCode.BAD_REQUEST, status_text="Missing required eBPF parameters")
        try:
            prog_type = target.attach_type.Name.lower() if target.attach_type else None
            prog = self.manager.create_program(
                prog_type,
                prog_path=target.file.Name,
                section=target.file.Section,
                direction=target.direction.Name.lower()
            )
            prog.remove(ifaces=target.interfaces.Names if target.interfaces else None)
            
            return Response(status=StatusCode.OK, status_text="Program has been deleted successfully")
        except Exception as e:
            self.logger.exception(e)
            return self.__servererror(cmd, e)

    def __notimplemented(self, cmd: Command):
        return Response(StatusCode.NOTIMPLEMENTED, status_text = f'Action {cmd.action.name} not implemented')

    def __servererror(self, cmd, e):
        """ Internal server error

            Default response in case something goes wrong while processing the command.

            :param cmd: The command that triggered the error.
            :param e: The Exception returned.
            :return: A standard INTERNALSERVERERROR response.
        """
        if(logging.root.level < logging.INFO):
            return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error: ' + str(e))
        else:
            return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error')