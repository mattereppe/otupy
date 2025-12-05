import logging
import time
from otupy import Version, StatusCode
from otupy import  StatusCodeDescription, Actions, Command, Response
from otupy.profiles.ebpf.targets.eBPFload_target import eBPFload_file_target
import ctypes as ct
from otupy.actuators.Ebpf.manager_eBPF import EBPFManager



logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)


MY_IDS = {
	'domain': None,
	'asset_id': None
}

class EbpfActuator:
    
    domain : str = None
    asset_id : str = None
    
    def run(self, cmd: Command) -> Response:
        """ Dispatches the OpenC2 command to the appropriate action method. """
        try:
            match cmd.action:
                case Actions.create:
                    return self.create(cmd)
                case _:
                    return self.__notimplemented(cmd)
        except Exception as e:
            return self.__servererror(cmd, e)



    def create(self, cmd):
        """
        Create (attach) an eBPF program via EBPFManager.
        """
        # Get the ebpf_program object from the command
        obj: eBPFload_file_target = cmd.target.getObj()

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
        except Exception as e:
            return Response(
                status=StatusCode.INTERNAL_ERROR,
                status_text=f"Failed to attach eBPF program: {e}"
            )

        return Response(
            status=StatusCode.OK,
            status_text="Programma BPF agganciato con successo (CREATE)."
        )

    
    
    def __notimplemented(self, cmd: Command):
        return Response(status=StatusCode.NOTIMPLEMENTED, status_text=f'Action {cmd.action.name} not implemented')

    def __servererror(self, cmd: Command, e: Exception):
        logger.error(f"Internal Error processing command {cmd.action.name}: {e}", exc_info=True)
        return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error')