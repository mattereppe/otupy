
import subprocess

from otupy import    Command, Response
import logging

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

        required = ["Direction", "AttachType", "Interfaces", "maps"]
        missing = [k for k in required if k not in arguments]

        if missing:
            return badrequest(
                status_text=f"Missing required parameters: {', '.join(missing)}"
            )

        load(
            ifaces=arguments["Interfaces"],
            prog_path=target.file.Name,
            section=target.file.Section,
            direction=arguments["Direction"].Name,
            storage=arguments.get("storage"),
            isUri=target.file.isUri,
            attach_type=arguments["AttachType"].Name,
            maps=arguments.get("maps")
        )

        return ok("Program loaded successfully")

    except ValueError as e:
        return badrequest(status_text=str(e))

    except Exception as e:
        logger.exception("Unhandled error in create()")
        return servererror("Internal server error")

def copy(storage: File = None, isUri: bool = False, prog_path: str = None):
    try:
        pf = rcli.Specifiers({})

        arg = rcli.Args(
            {
                "storage": File(
                    {
                        "path": storage.get("path"),
                        "name": storage.get("name"),
                    }
                )
            }
        )

        if isUri:
            artifact = oc2.Artifact(
                mime_type="application/json",
                payload=oc2.Payload(URI(prog_path)),
            )

        else:
            if not prog_path:
                raise ValueError("prog_path is required when isUri=False")

            try:
                with open(prog_path, "rb") as f:
                    bcontent = f.read()
            except FileNotFoundError as e:
                raise FileNotFoundError(f"File not found: {prog_path}") from e
            except IOError as e:
                raise IOError(f"Error reading file: {prog_path}") from e

            hashes = oc2.Hashes(
                {"md5": oc2.Binaryx(hashlib.md5(bcontent).digest())}
            )

            artifact = oc2.Artifact(
                mime_type="application/json",
                payload=oc2.Binary(bcontent),
                hashes=hashes,
            )

        cmd = oc2.Command(oc2.Actions.copy, artifact, arg, actuator=None)

        return copy_rcli(cmd)

    except Exception as e:
        raise RuntimeError("Copy operation failed") from e

def load(
    ifaces: Interfaces = None,
    storage: File = None,
    prog_path: str = None,
    section: str = None,
    direction: str = None,
    isUri: bool = False,
    attach_type: str = None,
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

            # Copy file
            response: Response = copy(
                storage=storage,
                isUri=isUri,
                prog_path=prog_path,
            )

            if response.get("status") != StatusCode.OK:
                raise RuntimeError("Error copying file to target location")

            results = response["results"]["file_status"][0]

            full_path = os.path.join(
                results.get("path"),
                results.get("name"),
            )

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
                        full_path,
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
                file_path=full_path,
                file_name=os.path.basename(full_path),
                calculated_hash=str(results["hashes"]["md5"]),
                attach_type=attach_type,
                direction=direction,
                Section=section,
                interface=iface,
                maps=str(maps)
            )

    except Exception as e:
        raise RuntimeError("Error during program loading") from e
        
