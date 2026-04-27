from imaplib import Commands

from otupy import   Actions, Command, Response

from otupy.core.actuator import actuator_implementation

from otupy.profiles.ebpf.validation.TCHookValidation import validate_command, validate_args




from otupy.actuators.ebpf.response_handler import servererror, badrequest, notimplemented, notfound, ok
from otupy.types.data.version import Version




from otupy.actuators.ebpf.actuators.TC.actions.query import query
from otupy.actuators.ebpf.actuators.TC.actions.delete import delete
from otupy.actuators.ebpf.actuators.TC.actions.create import create
from otupy.actuators.ebpf.actuators.TC.actions.copy import copy

""" Supported OpenC2 Version """
OPENC2VERS = Version(1, 0)

@actuator_implementation("ebpf-TC")
class TCActuator():
    def __init__(self,  **kwargs):

        self.auth = kwargs['auth'] if 'auth' in kwargs else None
        self.config = kwargs['config'] if 'config' in kwargs else None
        self.peers = kwargs['peers'] if 'peers' in kwargs else None
        self.owner = kwargs['owner'] if 'owner' in kwargs else None
        self.specifiers = kwargs['specifiers'] if 'specifiers' in kwargs else None


    def run(self, cmd: Command) -> Response:
        if not validate_command(cmd):
            return notimplemented( status_text='Invalid Action/Target pair')
        if not validate_args(cmd):
            return badrequest(status_text='Invalid or missing arguments for the given Action/Target pair')
        try:
            if not self._is_addressed_to_actuator(cmd.actuator.getObj()):
                return notfound(status_text='Requested Actuator not available')
        except AttributeError:
            
            pass
        except Exception as e:
            return servererror(status_text='Unable to identify actuator')
        match cmd.action:
            case Actions.copy: return copy(cmd)
            case Actions.create: return create(cmd)
            case Actions.query: return query(cmd)
            case Actions.delete: return delete(cmd)
            case _: return self.__notimplemented(cmd)

    def _is_addressed_to_actuator(self, actuator) -> bool:
        """ Checks if this Actuator must run the command """
        if actuator is None or len(actuator) == 0:
            
            return True

        for k,v in actuator.items():		
            try:
                # For now, just check if the asset_id matches
                if(v == self.specifiers['asset_id']):
                    return True
            except KeyError:
                pass

        return False

    
    def __notimplemented(self, cmd: Command) -> Response:
        return notimplemented(f'Action {cmd.action.name} not implemented')
    

