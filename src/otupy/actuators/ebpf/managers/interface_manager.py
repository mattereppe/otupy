from typing import List


class InterfaceManager:
    def __init__(self, executor):
        self.executor = executor

    def list_up(self) -> List[str]:
        """
        List all network interfaces that are currently 'up'.
        Uses the 'ip' command and parses the output to return interface names.
        """
        cp = self.executor.run_cmd("ip -o l show up")
        return [line.split(": ")[1].split()[0] for line in cp.stdout.splitlines()]

    def ensure_clsact(self, iface: str) -> bool:
        """
        Ensure that the 'clsact' qdisc exists on a given interface.
        'clsact' allows attaching ingress/egress filters or eBPF programs
        without affecting normal packet handling.

        Returns:
        True if 'clsact' was already present or added successfully.
        False if adding 'clsact' failed.
        """
        try:


            cp = self.executor.run_cmd(f"tc qdisc show dev {iface} handle ffff:", capture_output=True)
            if "clsact" in cp.stdout:
                return True
            self.executor.run_cmd(f"tc qdisc add dev {iface} clsact", check=True)
            return True 
        except Exception as e:
            return False