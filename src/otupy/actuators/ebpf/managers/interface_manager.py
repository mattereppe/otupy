from typing import List
"""
Maybe can created an abstract class 
BaseInterfaceManager

"""
class InterfaceManager:
    def __init__(self, executor):
        self.executor = executor

    def list_up(self) -> List[str]:
        cp = self.executor.run_cmd("ip -o l show up")
        return [line.split(": ")[1].split()[0] for line in cp.stdout.splitlines()]

    def ensure_clsact(self, iface: str):
        cp = self.executor.run_cmd(f"tc qdisc show dev {iface} handle ffff:", capture_output=True)
        if "clsact" not in cp.stdout:
            self.executor.run_cmd(f"tc qdisc add dev {iface} clsact", check=True)