
import subprocess

from otupy import    Command, Response
import logging

from otupy.core import results
from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program


from otupy.actuators.ebpf.response_handler import servererror, badrequest, notimplemented, notfound, ok

from otupy.types.base.array_of import ArrayOf
from otupy.types.data.version import Version

import os

from otupy.actuators.ebpf.managers.interface_manager import InterfaceManager
from otupy.actuators.ebpf.executors.TC_command_executor import TCCommandExecutor

from otupy import Response, StatusCode
from otupy.actuators.rcli.user.config import PRODUCER_ID

from otupy.actuators.ebpf.actuators.TC.database.SQLDB import db
from otupy.actuators.rcli.database.SQLDB import db as rcli_db
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces


import otupy as oc2
from otupy.actuators.rcli.actions.copy import copy as copy_rcli
from otupy.profiles import rcli
from otupy.types.targets.file import File
from otupy.types.data.uri import URI
import hashlib


logger = logging.getLogger(__name__)

""" Supported OpenC2 Version """
OPENC2VERS = Version(1, 0)


def create(cmd: Command) -> Response:
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
 

        result = rcli_db.retrieve_file(PRODUCER_ID, target.file.file_path,target.file.file_name)
        if not result:
            return notfound(status_text="eBPF file not found in database ")
        for row in result:
   
            uid, f_path, f_name, calculated_hash = row
            load(
                file_path=f_path,
                file_name=f_name,
                section=target.file.Section if target.file else None,
                direction=arguments.get("Direction").Name if arguments.get("Direction") else None,
                attach_type=arguments.get("AttachType").Name if arguments.get("AttachType") else None,
                maps=arguments.get("maps") if arguments.get("maps") else None,
                hash=calculated_hash,
                ifaces=(
                arguments.get("Interfaces")
                if arguments.get("Interfaces")
                else None
            )
            )

        return ok("Program loaded successfully")

    except ValueError as e:
        return badrequest(status_text=str(e))

    except Exception as e:
        logger.exception("Unhandled error in create()")
        return servererror("Internal server error")

def load(
    ifaces: Interfaces = None,
    file_path: str = None,
    file_name: str = None,
    section: str = None,
    direction: str = None,
    attach_type: str = None,
    hash:str = None,
    maps= None
):
    executor = TCCommandExecutor()
    iface_mgr = InterfaceManager(executor)

    if not ifaces or not ifaces.Names:
        raise ValueError("No interfaces provided")

    try:
        for iface in ifaces.Names:

            # Ensure clsact
            if not iface_mgr.ensure_clsact(iface):
                raise RuntimeError(f"Cannot ensure clsact on interface {iface}")


            # Run tc command
            try:
                executor.run_cmd(
                    [
                        "tc",
                        "filter",
                        "add",
                        "dev",
                        iface,
                        direction,
                        "bpf",
                        "da",
                        "obj",
                        os.path.join(file_path, file_name),
                        "sec",
                        section,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"tc command failed on interface {iface}"
                ) from e

            # Store metadata
            db.add_hookpoint(
                uid=PRODUCER_ID,
                file_path=file_path,
                file_name=file_name,
                calculated_hash=hash,  # Hash calculation can be added here if needed
                attach_type=attach_type,
                direction=direction,
                Section=section,
                interface=iface,
                maps=str(maps)
            )

    except Exception as e:
        raise RuntimeError("Error during program loading") from e
        
