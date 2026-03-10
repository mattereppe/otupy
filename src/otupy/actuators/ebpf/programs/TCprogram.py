import os
from typing import List, Optional

from otupy.actuators.ebpf.managers.interface_manager import InterfaceManager
from otupy.actuators.ebpf.base.ebpf_base import BaseEBPFProgram
from otupy.actuators.ebpf.executors.TC_command_executor import TCCommandExecutor
import re

class TCProgram(BaseEBPFProgram):
    def __init__(
            self,
            prog_path: str | None = None,
            section: str | None = None,
            direction: str | None = None
        ):
            self.prog_path = prog_path
            self.section = section
            self.direction = direction
            self.executor = TCCommandExecutor() 

    def load(self, iface: str = None):
        iface_mgr = InterfaceManager(self.executor)
        if iface_mgr.ensure_clsact(iface):

            
            self.executor.run_cmd([
                "tc", "filter", "add", "dev", iface, self.direction,
                "bpf", "da", "obj", self.prog_path, "sec", self.section
            ], check=True)
        else:
            raise Exception("Cannot ensure clasct")

    def remove(self, ifaces: Optional[List[str]] = None):
        iface_mgr = InterfaceManager(self.executor)
        prog_name = os.path.basename(self.prog_path)
        for iface in ifaces:
            cp = self.executor.run_cmd(["tc", "filter", "show", "dev", iface, self.direction], check=False)

            for line in cp.stdout.splitlines():
                if prog_name in line:
                    m = re.search(r"pref\s+(\d+)", line)
                    if m:
                        pref = m.group(1)
                        self.executor.run_cmd([
                            "tc", "filter", "del", "dev", iface, self.direction,
                            "protocol", "all", "pref", pref, "bpf"
                        ], check=False)
    def query(
        self,
        file: str = None,
        direction: str = None,
        attach_type: str = None,
        interfaces: Optional[List[str]] = None
    ) -> List[dict]:

        iface_mgr = InterfaceManager(self.executor)

        ifaces = interfaces or iface_mgr.list_up()
        dirs = [direction] if direction else ["ingress", "egress"]

        results = []

        for iface in ifaces:
            for d in dirs:

                cp = self.executor.run_cmd(
                    ["tc", "filter", "show", "dev", iface, d],
                    check=False
                )

                for line in cp.stdout.splitlines():

                    # get preference
                    pref_match = re.search(r"pref\s+(\d+)", line)
                    if not pref_match:
                        continue
                    pref = pref_match.group(1)

                    # get file and section
                    file_match = re.search(r"(\S+\.o)(?::\[(\S+)\])?", line)
                    if not file_match:
                        continue  # skip placeholder / empty filters
                    obj = file_match.group(1) if file_match else None
                    section = file_match.group(2) if file_match else None

                    # get program name
                    prog_match = re.search(r"name\s+(\S+)", line)
                    program_name = prog_match.group(1) if prog_match else None

                    record = {
                        "interface": iface,
                        "direction": d,
                        "pref": pref,
                        "file": obj,
                        "section": section,
                        "program": program_name,
                        "attach_type": attach_type or "tc"
                    }

                    # filtering by file name if requested
                    if file and obj:
                        if os.path.basename(obj) != os.path.basename(file):
                            continue

                    results.append(record)

        return results