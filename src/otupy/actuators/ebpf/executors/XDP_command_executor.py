import logging
import subprocess
import shlex
from typing import List, Union
from otupy.actuators.ebpf.base.base_command_executor import BaseCommandExecutor

class XDPCommandExecutor(BaseCommandExecutor):
    """Executor for XDP eBPF programs with logging."""

    FORBIDDEN_CHARS = set(";|&$><`\\")
    DANGEROUS_PATTERNS = [r"\.\.", r"\s", r"[;&|`]"]

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("XDPCommandExecutor")

    @staticmethod
    def secure_validate_token(token: str, allow_abs: bool = True) -> None:
        """Validate command token for shell safety."""
        if not isinstance(token, str):
            raise TypeError("Command token must be str")

        if any(c in token for c in XDPCommandExecutor.FORBIDDEN_CHARS):
            raise ValueError(f"Forbidden character in token: {token}")

        import re
        for pat in XDPCommandExecutor.DANGEROUS_PATTERNS:
            if re.search(pat, token):
                raise ValueError(f"Unsafe token detected: {token}")

        if (not allow_abs) and (token.startswith("/") or token.startswith("~")):
            raise ValueError("Absolute path not allowed")

    @staticmethod
    def secure_middleware(args: List[str]) -> List[str]:
        """Validate all command arguments."""
        if not isinstance(args, (list, tuple)):
            raise TypeError("Command must be list/tuple")
        for token in args:
            XDPCommandExecutor.secure_validate_token(token)
        return list(args)

    def run_cmd(
        self, cmd: Union[str, List[str]], check: bool = True, capture_output: bool = True
    ):
        """Run XDP commands safely with logging."""
        args = list(cmd) if isinstance(cmd, (list, tuple)) else shlex.split(cmd)
        args = self.secure_middleware(args)

        self.logger.debug(f"Running XDP command: {' '.join(args)}")
        try:
            result = subprocess.run(
                args,
                check=check,
                capture_output=capture_output,
                text=True
            )
            if capture_output:
                self.logger.debug(f"stdout: {result.stdout.strip()}")
                self.logger.debug(f"stderr: {result.stderr.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"XDP command failed: {e.stderr.strip() if e.stderr else e}")
            raise