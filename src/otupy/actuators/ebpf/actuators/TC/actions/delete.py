
from otupy import    Command, Response
import logging

from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program


from otupy.actuators.ebpf.response_handler import servererror, badrequest, notimplemented, notfound, ok

from otupy.types.data.version import Version


from otupy.actuators.ebpf.programs.TCprogram import TCProgram




logger = logging.getLogger(__name__)

""" Supported OpenC2 Version """
OPENC2VERS = Version(1, 0)


def delete(cmd: Command) -> Response:
    target : eBPF_program= cmd.target.getObj()
    if target.file is None or target.direction is None or target.attach_type is None or target.interfaces is None:
        return badrequest(status_text="Missing required eBPF parameters")

    manager = TCProgram(
        prog_path=target.file.Name if target.file else None,
        section=target.file.Section if target.file else None,
        direction=target.direction.Name.lower() if target.direction else None
    )
    try:
        manager.remove(ifaces=target.interfaces.Names if target.interfaces else None)
        return ok("Program has been deleted successfully")
    except Exception as e:
        
        return servererror("Server error while processing command", e)