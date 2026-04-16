
from otupy import    Command, Response
import logging

from otupy.profiles import ebpf
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.query_results import QueryResults
from otupy.types.base.array_of import ArrayOf


from otupy import ResponseType, Results
from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program


from otupy.actuators.ebpf.response_handler import servererror, badrequest, notimplemented, notfound, ok
from otupy.types.data.feature import Feature
from otupy.types.data.nsid import Nsid
from otupy.types.data.version import Version
from otupy.types.targets.features import Features

from otupy.actuators.ebpf.programs.TCprogram import TCProgram

logger = logging.getLogger(__name__)

""" Supported OpenC2 Version """
OPENC2VERS = Version(1, 0)



def query(cmd: Command) -> Response:
        

    logger.info(f"Querying action with command: {cmd}")
    if cmd.args is not None:
        try:
            if cmd.args.get("response_requested") is not None:
                if not (cmd.args["response_requested"] == ResponseType.complete):
                    raise KeyError
        except KeyError:
            return badrequest("Invalid query argument")
    
    
    
    if cmd.target.getObj().__class__ == Features:
        r = query_feature(cmd)
    elif cmd.target.getObj().__class__ == eBPF_program:
        r = query_tc(cmd)
    else:
        return badrequest("Target not supported.")
    return r

@staticmethod
def query_tc(cmd):


    target : eBPF_program  = cmd.target.getObj()
    
    
    prog_type = target.attach_type.Name.lower()
    manager = TCProgram(
        prog_path=target.file.Name if target.file else None,
        section=target.file.Section if target.file else None,
        direction=target.direction.Name.lower() if target.direction else None
    )
    try:
       
        programs = manager.query(attach_type = prog_type)
        

        program_files = [ProgramFile(Program=p["file"], Section=p.get("section")) for p in programs]
        results = QueryResults(
            Program=ArrayOf(ProgramFile)(program_files),
            hook_point=ArrayOf(AttachType)([p["attach_type"] for p in programs]),
            Direction=ArrayOf(Direction)([p["direction"] for p in programs]),
            Interfaces=ArrayOf(Interfaces)([p["interface"] for p in programs])
        )
        return ok("{len(programs)} programs loaded",res=results)
        
    except Exception as e:
        
        return servererror("Server error while processing command", e)

@staticmethod
def query_feature(cmd):
    """
    Handles the query for supported features, such as OpenC2 versions, profiles, and allowed command targets.

    Implements the 'query features' command, returning the features supported by the OpenC2 actuator.
    The supported features include OpenC2 versions, profiles, and allowed command targets. If a feature is not
    implemented, a `notimplemented` response is returned.

    Args:
        cmd (Command): The `Command` object containing:
            - `target`: The target of the query, which should be of type `Features`.
            - `args`: A dictionary of optional arguments.

    Returns:
        Response: A response indicating the result of the query action:
            - `ok`: If the query was successful.
            - `notimplemented`: If a feature is not implemented or invalid feature is requested.
            - `servererror`: If an error occurs while processing the command, such as a database or internal failure.

    Example:
        cmd = Command(target=Features(), args={})
        query_feature(cmd)
    """
    logger.info(f"Querying features with command: {cmd}")
    features = {}
    for f in cmd.target.getObj():
        match f:
            case Feature.versions:
                features[Feature.versions.name] = ArrayOf(Version)([OPENC2VERS])
            case Feature.profiles:
                pf = ArrayOf(Nsid)()
                pf.append(Nsid(ebpf.Profile.nsid))
                features[Feature.profiles.name] = pf
            case Feature.pairs:
                features[Feature.pairs.name] = ebpf.AllowedCommandTarget
            case Feature.rate_limit:
                return notimplemented("Feature 'rate_limit' not yet implemented")
            case _:
                return notimplemented("Invalid feature '" + f + "'")
        res = None
    try:
        res = Results(features)
        return ok("Ok", res=res)
    except Exception as e:
        return servererror("Server error while processing command", e)