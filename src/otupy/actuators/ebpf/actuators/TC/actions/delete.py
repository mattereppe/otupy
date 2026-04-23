
import subprocess
import os
import otupy as oc2
from otupy import    Command, Response
import logging

from otupy.actuators.ebpf.executors.TC_command_executor import TCCommandExecutor
from otupy.actuators.rcli.user.config import PRODUCER_ID
from otupy.profiles import rcli
from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program


from otupy.actuators.ebpf.response_handler import servererror, badrequest, notimplemented, notfound, ok

from otupy.profiles.rcli.targets.files import Files
from otupy.types.data.version import Version
from otupy.actuators.rcli.actions.delete import delete as delete_rcli
from otupy.actuators.ebpf.actuators.TC.database.SQLDB import db
import re

from otupy import Response, StatusCode
from otupy.types.targets.file import File


logger = logging.getLogger(__name__)

""" Supported OpenC2 Version """
OPENC2VERS = Version(1, 0)

def delete_from_rcli(path: str = None, name_file: str = None):
    try:
        pf = rcli.Specifiers({})

  
        files = Files()
        files.append(File({"path": path, "name": name_file}))

        cmd = oc2.Command(oc2.Actions.delete, files, None, actuator=pf)
        return delete_rcli(cmd)
    except ValueError as e:
        return badrequest(status_text=str(e))

    except Exception:
        logger.exception("Unhandled error in delete()")
        return servererror("Internal server error")
        


def delete(cmd: Command) -> Response:
    try:
        target: eBPF_program = cmd.target.getObj()

        if not target.file:
            return badrequest(status_text="Missing required eBPF file")

        arguments = cmd.args or {}

        required = ["Direction", "AttachType", "Interfaces"]
        missing = [k for k in required if k not in arguments]

        if missing:
            return badrequest(
                status_text=f"Missing required parameters: {', '.join(missing)}"
            )

        remove(
            ifaces=arguments["Interfaces"],
            prog_path=target.file.Name,
            section=target.file.Section,
            direction=arguments["Direction"].Name,
            attach_type=arguments["AttachType"].Name,
        )

        return ok("Program has been deleted successfully")

    except ValueError as e:
        return badrequest(status_text=str(e))

    except Exception:
        logger.exception("Unhandled error in delete()")
        return servererror("Internal server error")

def remove(
    ifaces,
    prog_path=None,
    direction=None,
    section=None,
    attach_type=None,
):
    executor = TCCommandExecutor()

    if not ifaces or not ifaces.Names:
        raise ValueError("No interfaces provided")

    if not prog_path:
        raise ValueError("prog_path is required")

    prog_name = os.path.basename(prog_path)

    try:
        for iface in ifaces.Names:

            # Check if exists in DB
            exists = db.exists_file(
                uid=PRODUCER_ID,
                file_path=prog_path,
                file_name=prog_name,
                attach_type=attach_type,
                direction=direction,
                Section=section,
                interface=iface,
            )

            if not exists:
                logger.warning(
                    f"No hookpoint found for {prog_name} on {iface}"
                )
                continue

            # Show tc filters
            try:
                cp = executor.run_cmd(
                    ["tc", "filter", "show", "dev", iface, direction],
                    check=False,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Failed to list tc filters on {iface}"
                ) from e

            # Find and delete matching filters
            for line in cp.stdout.splitlines():
                if prog_name in line:
                    match = re.search(r"pref\s+(\d+)", line)
                    if match:
                        pref = match.group(1)

                        try:
                            executor.run_cmd(
                                [
                                    "tc",
                                    "filter",
                                    "del",
                                    "dev",
                                    iface,
                                    direction,
                                    "protocol",
                                    "all",
                                    "pref",
                                    pref,
                                    "bpf",
                                ],
                                check=False,
                            )
                        except subprocess.CalledProcessError as e:
                            raise RuntimeError(
                                f"Failed to delete filter on {iface}"
                            ) from e

            # Remove from DB
            db.delete_hookpoint(
                uid=PRODUCER_ID,
                file_path=prog_path,
                file_name=prog_name,
                attach_type=attach_type,
                direction=direction,
                Section=section,
                interface=iface,
            )
            logger.info(
                f"Deleted hookpoint for {prog_name} on {iface} ({direction})"
            )
            
            response = delete_from_rcli(
                path=os.path.dirname(prog_path),
                name_file=prog_name,)
            
            if response.get("status") != StatusCode.OK:
                raise RuntimeError("Error deleting file from target location")
            logger.info(
                f"Deleted file from the filesystem"
            )
            

    except Exception as e:
        raise RuntimeError("Error during program deletion") from e