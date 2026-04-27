

from otupy.core.actions import Actions
from otupy.profiles.ebpf.profile import Profile
from otupy.types.data.action_targets import ActionTargets
from otupy.types.data.target_enum import TargetEnum


from otupy import Actions, StatusCode, ActionTargets, ActionArguments, TargetEnum, ResponseType
from otupy.types.targets.features import Features

AllowedStatusCode = [
    StatusCode.PROCESSING,
    StatusCode.OK,
    StatusCode.BADREQUEST,
    StatusCode.UNAUTHORIZED,
    StatusCode.FORBIDDEN,
    StatusCode.NOTFOUND,
    StatusCode.INTERNALERROR,
    StatusCode.NOTIMPLEMENTED,
    StatusCode.SERVICEUNAVAILABLE,
]
""" List of allowed status code in `Response` """
AllowedActions = [ Actions.create, Actions.delete, Actions.query, Actions.copy]
AllowedCommandTarget = ActionTargets()
""" List of allowed `Target` for each `Action`

	 Command Matrix: valid Command/Target pairs
"""


AllowedCommandTarget[Actions.query] = [TargetEnum.features,TargetEnum.artifact,TargetEnum[Profile.nsid+':eBPF_program']]

AllowedCommandTarget[Actions.create] = [TargetEnum[Profile.nsid+':eBPF_program']]
AllowedCommandTarget[Actions.delete] = [TargetEnum[Profile.nsid+':eBPF_program']]
AllowedCommandTarget[Actions.copy] = [TargetEnum.artifact]


AllowedCommandArguments = ActionArguments()
AllowedCommandArguments[(Actions.copy, TargetEnum.artifact)] = ["response_requested", "storage"]
AllowedCommandArguments[(Actions.create, TargetEnum[Profile.nsid+':eBPF_program'])] = ["Direction", "AttachType", "Interfaces", "maps"]
AllowedCommandArguments[(Actions.query, TargetEnum[Profile.nsid+':eBPF_program'])] = ["Direction", "AttachType", "Interfaces", "maps","maps_required"]
AllowedCommandArguments[(Actions.delete, TargetEnum[Profile.nsid+':eBPF_program'])] = ["Direction", "AttachType", "Interfaces"]


def validate_command(cmd):
	""" Validate a `Command` 

		Helper function to check the `Target` in a `Command` are valid for the `Action` according
		to the EBPF profile for TC.
		:param cmd: The `Command` class to validate.
	""" 
	
	try:
		if cmd.action in AllowedActions and \
			TargetEnum[cmd.target.getName()] in AllowedCommandTarget[cmd.action]:
			return True
		else:
			return False
	except:
		return False
	
def validate_args(cmd):
    """Validate a `Command`

    Helper function to check the `Args` in a `Command` are valid for the `Action` and `Target`  according
    to the eBPF profile.
    :param cmd: The `Command` class to validate.
    """
    try:
        if cmd.args is None:
            return True
        for k, v in cmd.args.items():
            if k not in AllowedCommandArguments[cmd.action, TargetEnum[cmd.target.getName()]]:
                return False
        return True
    except:
        return False