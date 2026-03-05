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

    def load(self, ifaces: Optional[List[str]] = None):
        iface_mgr = InterfaceManager(self.executor)
        for iface in ifaces or iface_mgr.list_up():
            iface_mgr.ensure_clsact(iface)
            self.executor.run_cmd([
                "tc", "filter", "add", "dev", iface, self.direction,
                "bpf", "da", "obj", self.prog_path, "sec", self.section
            ], check=True)

    def remove(self, ifaces: Optional[List[str]] = None):
        iface_mgr = InterfaceManager(self.executor)
        prog_name = os.path.basename(self.prog_path)
        for iface in ifaces or iface_mgr.list_up():
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

                    pref_match = re.search(r"pref\s+(\d+)", line)
                    if not pref_match:
                        continue

                    pref = pref_match.group(1)

                    obj_match = re.search(r"obj\s+(\S+)", line)
                    obj = obj_match.group(1) if obj_match else None

                    sec_match = re.search(r"sec\s+(\S+)", line)
                    section = sec_match.group(1) if sec_match else None

                    record = {
                        "interface": iface,
                        "direction": d,
                        "pref": pref,
                        "file": obj,
                        "section": section,
                        "attach_type": attach_type or "tc"
                    }

                    # filtering
                    if file and obj:
                        if os.path.basename(obj) != os.path.basename(file):
                            continue

                    results.append(record)

        return results