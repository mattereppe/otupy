import logging
from otupy import Version, StatusCode
from otupy import   Actions, Command, Response
from otupy.actuators.ebpf.base.base_ebpf_actuator import BaseEBPFActuator
from otupy.actuators.ebpf.programs.KprobeProgram import KprobeProgram
from otupy.actuators.ebpf.managers.ebpf_program_manager import EBPFProgramManager
from otupy.core.actuator import actuator_implementation
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.query_results import QueryResults
from otupy.types.base.array_of import ArrayOf
from otupy.profiles.ebpf.validation.TCHookValidation import validate_command


from otupy.profiles.ebpf.targets.KprobeHook import ebpf_load_KPROBEprogram


@actuator_implementation("x-Kprobesebpf")
class KprobeActuator(BaseEBPFActuator):
    def __init__(self,  **kwargs):

        self.auth = kwargs['auth'] if 'auth' in kwargs else None
        self.config = kwargs['config'] if 'config' in kwargs else None
        self.peers = kwargs['peers'] if 'peers' in kwargs else None
        self.owner = kwargs['owner'] if 'owner' in kwargs else None
        self.specifiers = kwargs['specifiers'] if 'specifiers' in kwargs else None
        self.manager = EBPFProgramManager()
        self.manager.register_program_type("kprobe", KprobeProgram)
        self.logger = logging.getLogger(__name__)

    def run(self, cmd: Command) -> Response:
        match cmd.action:
            case Actions.create: return self.create(cmd)
            case Actions.query: return self.query(cmd)
            case Actions.delete: return self.delete(cmd)
            case _: return self.__notimplemented(cmd)
    
    def create(self, cmd: Command) -> Response:
        obj : eBPF_load_KprobeProgram  = cmd.target.getObj()
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