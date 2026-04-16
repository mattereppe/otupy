import subprocess
from typing import List, Union

from otupy.actuators.ebpf.base.base_command_executor import BaseCommandExecutor

class TCCommandExecutor(BaseCommandExecutor):
    """Executor for TC eBPF programs."""

    @staticmethod
    def secure_validate_token(token: str, allow_abs: bool = True) -> None:
        FORBIDDEN_CHARS = set(";|&$><`\\")
        DANGEROUS_PATTERNS = [r"\.\.", r"\s", r"[;&|`]"]

        if not isinstance(token, str):
            raise TypeError("Command token must be str")
        if any(c in token for c in FORBIDDEN_CHARS):
            raise ValueError(f"Forbidden character in token: {token}")

        import re
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, token):
                raise ValueError(f"Unsafe token detected: {token}")

        if (not allow_abs) and (token.startswith("/") or token.startswith("~")):
            raise ValueError("Absolute path not allowed")

    @classmethod
    def secure_middleware(cls, args: List[str], allow_abs: bool = True) -> List[str]:
        if not isinstance(args, (list, tuple)):
            raise TypeError("Command must be list/tuple")
        for token in args:
            cls.secure_validate_token(token, allow_abs)
        return list(args)

    def run_cmd(self, cmd: Union[str, List[str]], check: bool = True, capture_output: bool = True):
        args = list(cmd) if isinstance(cmd, (list, tuple)) else cmd.split()
        args = self.secure_middleware(args)
        return subprocess.run(args, check=check, capture_output=capture_output, text=True)