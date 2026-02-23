import os
from typing import List, Optional

from otupy.actuators.ebpf.managers.interface_manager import InterfaceManager
from otupy.actuators.ebpf.base.ebpf_base import BaseEBPFProgram
from otupy.actuators.ebpf.executors.TC_command_executor import TCCommandExecutor
import re

class TCProgram(BaseEBPFProgram):
    def __init__(self, prog_path: str, section: str, direction: str):
        self.prog_path = prog_path
        self.section = section
        self.direction = direction
        self.executor = TCCommandExecutor()  # fixed executor for TC programs

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

    def query(self) -> List[dict]: 
        # Return loaded programs per interface return []
        pass