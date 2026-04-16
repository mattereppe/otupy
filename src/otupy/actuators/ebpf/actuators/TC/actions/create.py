
from otupy import    Command, Response
import logging

from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program


from otupy.actuators.ebpf.response_handler import servererror, badrequest, notimplemented, notfound, ok

from otupy.types.data.version import Version


from otupy.actuators.ebpf.programs.TCprogram import TCProgram

import os
from typing import List, Optional

from otupy.actuators.ebpf.managers.interface_manager import InterfaceManager
from otupy.actuators.ebpf.base.ebpf_base import BaseEBPFProgram
from otupy.actuators.ebpf.executors.TC_command_executor import TCCommandExecutor
import re

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
    target : eBPF_program= cmd.target.getObj()
    if target.file is None:
        return badrequest(status_text="Missing required eBPF parameters")
    
    arguments = cmd.args
    
    if arguments is None or "Direction" not in arguments or "AttachType" not in arguments or "Interfaces" not in arguments:
        return badrequest(status_text="Missing required eBPF parameters")
    """
    manager = TCProgram(
        prog_path=target.file.Name if target.file else None,
        section=target.file.Section if target.file else None,
        direction=target.direction.Name.lower() if target.direction else None
    )
    """
    try:
        #manager.load(ifaces=target.interfaces)
        
        load(ifaces=arguments.get("Interfaces"), prog_path=target.file.Name if target.file else None,
            section=target.file.Section if target.file else None,
            direction=arguments.get("Direction").Name,
            storage=arguments.get("storage"),
            isUri=target.file.isUri if target.file else False
            )
            
        return ok("Program loaded successfully")
    except Exception as e:
        
        return servererror("Server error while processing command", e)
    
def copy(storage: File = None,isUri: bool = False, prog_path: str = None):
    pf = rcli.Specifiers({})

    arg = rcli.Args(
        {
            "storage": File({"path": storage.get("path"), "name": storage.get("name")})
        }
    )
    if isUri:
        uri = prog_path 
        a = oc2.Artifact(
            mime_type="application/json",
            payload=oc2.Payload(URI(uri)),
        )
    else:
        try:          
            with open(prog_path, "rb") as f:
                bcontent = f.read()
        except Exception as e:
            raise Exception("Cannot load binary content from file")
        
        h = oc2.Hashes({"md5": oc2.Binaryx(hashlib.md5(bcontent).digest())})
        a = oc2.Artifact(
            mime_type="application/json",
            payload=oc2.Binary(bcontent),
            hashes= h
        )

    cmd = oc2.Command(oc2.Actions.copy, a, arg, actuator=None)

    return copy_rcli(cmd)


def load(ifaces: Interfaces = None, storage: File = None,prog_path: str = None, section: str = None, direction: str = None, isUri: bool = False):
    executor = TCCommandExecutor() 
    iface_mgr = InterfaceManager(executor)
    try:
        for iface in ifaces.Names:

            if iface_mgr.ensure_clsact(iface):

                r: Response=copy(storage=storage, isUri=isUri, prog_path=prog_path)
                if r.get("status") != StatusCode.OK:
                    raise Exception("Error copying file to target location")
                results = r.get("results").get("file_status")
                full_path = os.path.join(results[0].get("path"), results[0].get("name"))
                
                
                executor.run_cmd([
                    "tc", "filter", "add", "dev", iface, direction,
                    "bpf", "da", "obj", full_path, "sec", section
                ], check=True)

                db.add_hookpoint(uid=PRODUCER_ID, file_path=full_path, file_name=os.path.basename(full_path), 
                            calculated_hash=str(results[0].get("hashes").get("md5")), attach_type="TC",
                             direction=direction, Section=section)
            else:
                raise Exception("Cannot ensure clasct")
    except Exception as e:
        raise Exception("Error during program loading: " + str(e))
        
