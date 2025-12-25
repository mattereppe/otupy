import logging
from otupy import Version, StatusCode
from otupy import  StatusCodeDescription, Actions, Command, Response
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.targets.eBPF_load_program import eBPF_load_program
from otupy.profiles.ebpf.targets.eBPF_query import eBPF_query
from otupy.actuators.ebpf.ebpf_manager import EBPFManager
from otupy.profiles.ebpf.query_results import QueryResults
from otupy.types.base.array_of import ArrayOf


logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)


MY_IDS = {
	'domain': None,
	'asset_id': None
}

class eBPFActuator:
    domain : str = None
    asset_id : str = None
    def __init__(self):
        
        EBPFManager.init(
            rundir="./tmp/ebpfmgr",
            json_logs=True,
            log_level=logging.DEBUG
        )


    
    def run(self, cmd: Command) -> Response:
        """ Dispatches the OpenC2 command to the appropriate action method. """
        try:
            match cmd.action:
                case Actions.create:
                    return self.create(cmd)
                case Actions.query:
                    return self.query(cmd)
                case Actions.delete:
                    return self.delete(cmd)
                case _:
                    return self.__notimplemented(cmd)
        except Exception as e:
            return self.__servererror(cmd, e)
        
    def delete(self,cmd: Command):
        
        try:
            target: eBPF_query = cmd.target.getObj()
            EBPFManager.remove_ebpf_program(
                ifaces=target.interfaces.Names if target.interfaces is not None else None,
                bpf_prog=target.file.Name if target.file is not None else None,
                attach_type=target.attach_type.Name.lower() if target.attach_type is not None else None,
                direction=target.direction.Name.lower() if target.direction is not None else None
            )
            return Response(
                status=StatusCode.OK,
                status_text=f"Program {target.file.Name} removed correctly"
            )
        except Exception as e:
            return Response(
                status=StatusCode.INTERNAL_ERROR,
                status_text=f"Failed to attach eBPF program: {type(e)}"
            )
            

    def query(self, cmd):
        """
        Docstring for query: retrieve the eBPF program loaded
        
        :param self: Description
        :param cmd: command from received
        """
        target: eBPF_query = cmd.target.getObj()
        # The query support empty value
        try:
            programs = EBPFManager.query_loaded_programs(
                iface=target.interfaces.Names if target.interfaces is not None else None,
                prog_name=target.file.Name if target.file is not None else None,
                attach_type=target.attach_type.Name.lower() if target.attach_type is not None else None
            )
            program_files = [
                ProgramFile(Program=p["program"], Section=p.get("section"))
                for p in programs]


            Results = QueryResults(
                Program=ArrayOf(ProgramFile)(program_files),
                hook_point= ArrayOf(AttachType)([p["attach_type"] for p in programs]),
                Direction=ArrayOf(Direction)([p["direction"] for p in programs]),
                Interfaces= ArrayOf(Interfaces)([p["interface"] for p in programs])

            )
            return Response(
                status=StatusCode.OK,
                status_text=f"Number of ebpf {len(programs)}",
                results = Results

            )
        except Exception as e:
            return Response(
                status=StatusCode.INTERNAL_ERROR,
                status_text=f"Failed to retrivies eBPF programs {type(e)}"
            )
            
    def create(self, cmd):
        """
        Create (attach) an eBPF program via EBPFManager.
        """
        # Get the ebpf_program object from the command
        obj: eBPF_load_program = cmd.target.getObj()

        # Validate required fields
        if obj.file is None or obj.direction is None or obj.attach_type is None:
            return Response(
                status=StatusCode.BAD_REQUEST,
                status_text="Missing required eBPF parameters: file, direction, attach_type"
            )

        
        
        # Load the BPF program
        #todo handle the interfaces
        try:
            EBPFManager.load_ebpf_program(
                ifaces=["wlp7s0"],
                bpf_prog=obj.file.Name, 
                section=obj.file.Section,
                direction=obj.direction.Name.lower(),
                attach_type=obj.attach_type.Name.lower()
            )
            return Response(
            status=StatusCode.OK,
            status_text="The program has been loaded in the kernel correctly"
        )
        except Exception as e:
            return Response(
                status=StatusCode.INTERNAL_ERROR,
                status_text=f"Failed to attach eBPF program: {type(e)}"
            )

 
    
            
            


    
    
    def __notimplemented(self, cmd: Command):
        return Response(status=StatusCode.NOTIMPLEMENTED, status_text=f'Action {cmd.action.name} not implemented')

    def __servererror(self, cmd: Command, e: Exception):
        logger.error(f"Internal Error processing command {cmd.action.name}: {e}", exc_info=True)
        return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error')