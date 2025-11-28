import logging
from otupy import Version, StatusCode
from otupy import  StatusCodeDescription, Actions, Command, Response
import otupy.profiles.ebpf as ebpf

logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)


MY_IDS = {
	'domain': None,
	'asset_id': None
}
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

    def create(self, cmd):
        # La logica è la stessa della tua precedente funzione LOAD
        file_path = cmd.target.ebpf_program.file_path
        kernel_hook = 'todo'
        # ... logica per l'aggancio BPF (Netlink/libbpf)
        print(f"[{self.id}] Esecuzione CREATE: Aggancio {file_path} a {kernel_hook}...")
        # ...
        return Response(status=StatusCode.OK, status_text=f"Programma BPF agganciato con successo (CREATE).")

    
    
    def __notimplemented(self, cmd: Command):
        return Response(status=StatusCode.NOTIMPLEMENTED, status_text=f'Action {cmd.action.name} not implemented')

    def __servererror(self, cmd: Command, e: Exception):
        logger.error(f"Internal Error processing command {cmd.action.name}: {e}", exc_info=True)
        return Response(status=StatusCode.INTERNALERROR, status_text='Internal server error')