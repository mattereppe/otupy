
import json
import ast
from otupy import    Command, Response
import logging
import os
from otupy.actuators.ebpf.executors.TC_command_executor import TCCommandExecutor
from otupy.profiles import ebpf
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.map_ebpf import MapeBPF
from otupy.profiles.ebpf.data.program_status import ProgramStatus
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.query_results import QueryResults
from otupy.types.base.array_of import ArrayOf


from otupy import ResponseType, Results
from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program
from otupy.actuators.ebpf.actuators.TC.database.SQLDB import db
from otupy.actuators.rcli.user.config import PRODUCER_ID

from otupy.actuators.ebpf.response_handler import servererror, badrequest, notimplemented, notfound, ok
from otupy.types.base.map_of import MapOf
from otupy.types.data.feature import Feature
from otupy.types.data.nsid import Nsid
from otupy.types.data.version import Version
from otupy.types.targets.features import Features


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
    executor = TCCommandExecutor()
    try:
        target: eBPF_program = cmd.target.getObj()
        arguments = cmd.args or {}
        
        # 1. Database Retrieval
        results = db.retrieve_hookpoints(
            uid=PRODUCER_ID,
            file_path=target.file.Name if target.file else None,
            file_name=os.path.basename(target.file.Name) if target.file else None,
            attach_type=arguments.get("AttachType").Name if arguments.get("AttachType") else None,
            direction=arguments.get("Direction").Name if arguments.get("Direction") else None,
            Section=target.file.Section if target.file else None,
            interface=(
                arguments.get("Interfaces").Names[0]
                if arguments.get("Interfaces") and arguments.get("Interfaces").Names
                else None
            )
        )

        prog_status = ArrayOf(ProgramStatus)()
        found_maps = ArrayOf(MapeBPF)()
        
        all_required_names = set()

        for row in results:
            # Using tuple unpacking for readability
            uid, f_path, f_name, h_val, a_type, d_rect, sect, iface, m_str = row
            

            
            # Collect all unique map names found in DB rows
            if m_str:
                try:
                    # Safely parse the map string (handle list or string format)
                    names = ast.literal_eval(m_str) if isinstance(m_str, str) else m_str
                    all_required_names.update(names)
                except (ValueError, SyntaxError):
                    logger.error(f"Failed to parse map string: {m_str}")

            # 2. BPFtool Lookup (Only if maps are required and found in DB)
            if arguments.get("maps_required") and all_required_names:
                result_cli = executor.run_cmd(["sudo", "bpftool", "map", "show", "-j"], capture_output=True, check=True)
                kernel_maps = json.loads(result_cli.stdout)
                
                # Build lookup dict: name -> id
                id_map = {m['name']: m['id'] for m in kernel_maps if 'name' in m}
                
                for name in all_required_names:
                    if name in id_map:
                        found_maps.append(MapeBPF(name=name, id=id_map[name]))
                    else:
                        logger.warning(f"Map '{name}' defined in DB but not found in kernel.")
            # 3. Build ProgramStatus for each DB row
            prog_status.append(ProgramStatus(
                Program=ProgramFile(file_path=f_path, file_name=f_name, Section=sect),
                Direction=Direction(d_rect),
                hook_point=AttachType(a_type),
                Interfaces=Interfaces([iface] if iface else []),
                maps=ArrayOf(MapeBPF)([m for m in found_maps if m.name in all_required_names]) if arguments.get("maps_required") else ArrayOf(MapeBPF)()
            ))
        res_data = QueryResults(
            program_status=prog_status
        )
        
        return ok(f"Programs found: {len(results)}", res=res_data)
        
    except Exception as e:
        logger.exception("Error in query_tc") # Logs the full stack trace
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