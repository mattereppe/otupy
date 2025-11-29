import logging
import time
from otupy import Version, StatusCode
from otupy import  StatusCodeDescription, Actions, Command, Response
import otupy.profiles.ebpf as ebpf
from bcc import BPF
import ctypes as ct

logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)


MY_IDS = {
	'domain': None,
	'asset_id': None
}
class Data(ct.Structure):
    _fields_ = [
    ("pid", ct.c_ulonglong),
    ("comm", ct.c_char * 16)
]
class EbpfActuator:
    
    # Internal state storage
    installed_programs = {}
    ebpf_maps = {} 
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


    def print_event(cpu, data, size):
        event = ct.cast(data, ct.POINTER(Data)).contents
        print("%-18.9f %-6d %s" % (time.time(), event.pid >> 32, event.comm.decode()))
    def create(self, cmd):


        source_code = cmd.target.obj.file_path
        hook_point = cmd.target.obj.prog_type
        b = BPF(text=source_code)

        #mi aggancio alla system che mi serve
        b.attach_kprobe(event=b.get_syscall_fnname(hook_point), fn_name="syscall__"+ hook_point)

        b["events"].open_perf_buffer(self.print_event)


        return Response(status=StatusCode.OK, status_text=f"Programma BPF agganciato con successo (CREATE).")

    
    
    def __notimplemented(self, cmd: Command):
        return Response(status=StatusCode.NOTIMPLEMENTED, status_text=f'Action {cmd.action.name} not implemented')

    def __servererror(self, cmd: Command, e: Exception):
        logger.error(f"Internal Error processing command {cmd.action.name}: {e}", exc_info=True)
        return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error')