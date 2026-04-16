import re
from typing import List, Dict
from otupy.actuators.ebpf.base.ebpf_base import BaseEBPFProgram
from otupy.actuators.ebpf.executors.XDP_command_executor import XDPCommandExecutor


class XDPProgram(BaseEBPFProgram):
    """Represents an XDP eBPF program."""

    def __init__(self, prog_path: str, section: str):
        self.prog_path = prog_path
        self.section = section
        self.executor = XDPCommandExecutor()
        self.logger = self.executor.logger

    def load(self, ifaces: List[str] = None) -> None:
        """Attach XDP program to interfaces."""
        ifaces = ifaces or self.list_up_interfaces()
        for iface in ifaces:
            cmd = [
                "ip", "link", "set", "dev", iface,
                "xdpgeneric", "obj", self.prog_path, "sec", self.section
            ]
            self.logger.info(f"Loading XDP program {self.prog_path} on {iface}")
            self.executor.run_cmd(cmd, check=True)

    def query(self, ifaces: List[str] = None) -> List[Dict]:
        """Query loaded XDP programs on interfaces."""
        ifaces = ifaces or self.list_up_interfaces()
        results = []

        for iface in ifaces:
            cmd = ["ip", "-d", "link", "show", iface]
            self.logger.debug(f"Querying XDP programs on {iface}")
            cp = self.executor.run_cmd(cmd, capture_output=True, check=False)
            # Match program names (e.g., "xdp prog id 123 name allow_all.o")
            matches = re.findall(r"xdp\s+prog\s+id\s+\d+\s+name\s+(\S+)", cp.stdout)
            for prog in matches:
                results.append({"interface": iface, "program": prog})
        return results

    def remove(self, ifaces: List[str] = None) -> None:
        """Detach XDP program from interfaces."""
        ifaces = ifaces or self.list_up_interfaces()
        for iface in ifaces:
            cmd = ["ip", "link", "set", "dev", iface, "xdpgeneric", "off"]
            self.logger.info(f"Removing XDP program from {iface}")
            self.executor.run_cmd(cmd, check=False)

    def list_up_interfaces(self) -> List[str]:
        """Helper: list all up interfaces (using ip)."""
        cmd = ["ip", "-o", "l", "show", "up"]
        self.logger.debug("Listing up interfaces")
        cp = self.executor.run_cmd(cmd, capture_output=True)
        return [line.split(": ")[1].split()[0] for line in cp.stdout.splitlines()]