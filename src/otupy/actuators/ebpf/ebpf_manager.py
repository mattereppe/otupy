#!/usr/bin/env python3
"""
Fully Static eBPF Manager
- Structured logging
- Runtime type checking
- Async support
- Full typing and docstrings
"""

from __future__ import annotations
import asyncio
import json
import re
import subprocess
import os
import shlex
import signal
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional, Callable, Any, Dict, TypedDict, Literal, Union
import warnings
import inspect
from functools import wraps

warnings.simplefilter("always", DeprecationWarning)

# -------------------------------------------------------
# Runtime type checking
# -------------------------------------------------------
def check_type(value: Any, expected: Any) -> bool:
    """Safely check if value matches expected type annotation."""
    from typing import get_origin, get_args, Union, Any as AnyType

    if expected in (AnyType, None):
        return True

    origin = get_origin(expected)
    args = get_args(expected)

    if origin is Union:
        return any(check_type(value, arg) for arg in args)

    if isinstance(expected, type):
        return isinstance(value, expected)

    # Cannot check generics like list[int]
    return True

def runtime_type_check(func: Callable) -> Callable:
    """Runtime argument + return type checking decorator."""
    sig = inspect.signature(func)
    annotations = func.__annotations__

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        # Check argument types
        for name, value in bound.arguments.items():
            if name in annotations:
                expected = annotations[name]
                if expected not in (None, Any):
                    if not check_type(value, expected):
                        raise TypeError(
                            f"{func.__name__}(): Argument '{name}' expected {expected}, got {type(value)}"
                        )

        result = func(*args, **kwargs)

        # Return type check
        if "return" in annotations:
            expected = annotations["return"]
            if not check_type(result, expected):
                raise TypeError(
                    f"{func.__name__}(): Return type expected {expected}, got {type(result)}"
                )

        return result

    return wrapper

# -------------------------------------------------------
# Logger Setup
# -------------------------------------------------------
def setup_logger(logfile: Path, json_logs: bool = False, level: int = logging.DEBUG) -> logging.Logger:
    """Setup a logger with optional JSON output."""
    logfile.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("EBPFManager")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    if json_logs:
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                return json.dumps({
                    "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                })
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)

    return logger

# -------------------------------------------------------
# TypedDict for query results
# -------------------------------------------------------
class LoadedProgram(TypedDict):
    interface: str
    attach_type: Literal["tc", "xdp"]
    section: Optional[str]  # may be None for XDP
    direction: Literal["ingress", "egress", "both", "-"]
    program: str

# -------------------------------------------------------
# EBPFManager
# -------------------------------------------------------
class EBPFManager:
    """
    Fully static eBPF manager with:
    - structured logging
    - runtime type checking
    - async/sync program management
    """

    # ------------------------
    # Static config
    # ------------------------
    RUNDIR: Path = Path("/var/run/ebpfmanager")
    PIDFILE: Path = RUNDIR / "userland.pid"
    IFACELIST: Path = RUNDIR / "iface.list"
    LOGGER: logging.Logger = setup_logger(RUNDIR / "ebpfmanager.log")

    # ------------------------
    # Initialization
    # ------------------------
    @classmethod
    @runtime_type_check
    def init(cls,
             rundir: str = "/var/run/ebpfmanager",
             pidfile: Optional[str] = None,
             log_level: int = logging.INFO,
             json_logs: bool = False
             ) -> None:
        """Initialize directories, PID files, and logging."""
        cls.RUNDIR = Path(rundir)
        cls.RUNDIR.mkdir(parents=True, exist_ok=True)

        cls.PIDFILE = Path(pidfile) if pidfile else cls.RUNDIR / "userland.pid"
        cls.IFACELIST = cls.RUNDIR / "iface.list"

        cls.LOGGER = setup_logger(
            logfile=cls.RUNDIR / "ebpfmanager.log",
            level=log_level,
            json_logs=json_logs
        )

        cls.LOGGER.info(f"EBPFManager initialized at {cls.RUNDIR}")

    # ------------------------
    # Security
    # ------------------------
    @staticmethod
    def secure_validate_token(token: str, allow_abs: bool = True) -> None:
        """Validate command token for shell safety."""
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

    @staticmethod
    def secure_middleware(args: List[str]) -> List[str]:
        """Validate all arguments for secure execution."""
        if not isinstance(args, (list, tuple)):
            raise TypeError("Command must be list/tuple")
        for token in args:
            EBPFManager.secure_validate_token(token)
        return list(args)

    # ------------------------
    # Command runners
    # ------------------------
    @staticmethod
    @runtime_type_check
    def run_cmd(
        cmd: Union[str, List[str]],
        check: bool = False,
        capture_output: bool = False,
        text: bool = True,
        ignore_errors: Optional[List[str]] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a synchronous command safely.

        Parameters:
            cmd: command string or list of arguments
            check: if True, raise CalledProcessError on non-zero return code
            capture_output: if True, capture stdout/stderr
            text: if True, treat stdout/stderr as strings
            ignore_errors: list of substrings in stderr to ignore (logs warning instead)

        Returns:
            subprocess.CompletedProcess
        """
        args = list(cmd) if isinstance(cmd, (list, tuple)) else shlex.split(cmd)
        args = EBPFManager.secure_middleware(args)
        EBPFManager.LOGGER.debug(f"Running command: {args}")

        try:
            result = subprocess.run(
                args,
                check=check,
                capture_output=capture_output,
                text=text
            )
            return result
        except subprocess.CalledProcessError as e:
            stderr_lower = (e.stderr or "").lower()
            ignored = ignore_errors or []

            for pattern in ignored:
                if pattern.lower() in stderr_lower:
                    EBPFManager.LOGGER.warning(f"Ignored error '{pattern}': {e.stderr.strip()}")
                    # Return a fake CompletedProcess with returncode=0
                    return subprocess.CompletedProcess(args=args, returncode=0, stdout=e.stdout, stderr=e.stderr)

            # Not ignored → raise
            EBPFManager.LOGGER.error(f"Command failed: {e.stderr.strip() if e.stderr else e}")
            raise

    @staticmethod
    async def run_cmd_async(cmd: Union[str, List[str]],
                            capture_output: bool = True,
                            text: bool = True) -> tuple[int, Optional[str], Optional[str]]:
        """Run async command safely."""
        args = list(cmd) if isinstance(cmd, (list, tuple)) else shlex.split(cmd)
        args = EBPFManager.secure_middleware(args)
        EBPFManager.LOGGER.debug(f"[async] Running command: {args}")
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            text=text
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout, stderr

    # ------------------------
    # Interfaces
    # ------------------------
    @staticmethod
    def get_dev_list_up() -> List[str]:
        """Return a list of interfaces that are up."""
        cp = EBPFManager.run_cmd("ip -o l show up", capture_output=True)
        return [line.split(": ")[1].split()[0] for line in cp.stdout.splitlines()]

    @staticmethod
    def ensure_clsact(dev: str) -> None:
        """Ensure a clsact qdisc is attached to device."""
        cp = EBPFManager.run_cmd(f"tc qdisc show dev {dev} handle ffff:", capture_output=True)
        if "clsact" not in cp.stdout:
            EBPFManager.run_cmd(f"tc qdisc add dev {dev} clsact", check=True)

    @staticmethod
    def filter_present(dev: str, direction: str, prog: str) -> bool:
        """Check if a TC BPF filter is present on device."""
        cp = EBPFManager.run_cmd(f"tc filter show dev {dev} {direction}", capture_output=True)
        return prog in cp.stdout

    @staticmethod
    def add_filter(dev: str, direction: str, prog: str, section: str) -> None:
        """Add TC BPF filter to device."""
        EBPFManager.run_cmd([
            "tc", "filter", "add", "dev", dev, direction,
            "bpf", "da", "obj", prog, "sec", section
        ], check=True)

    @staticmethod
    def del_filters(dev: str) -> None:
        """Delete all TC filters on a device."""
        for d in ("ingress", "egress"):
            EBPFManager.run_cmd(["tc", "filter", "del", "dev", dev, d], check=False)

    @classmethod
    def write_iface_list(cls, ifaces: List[str]) -> None:
        """Save interfaces to IFACELIST."""
        cls.RUNDIR.mkdir(parents=True, exist_ok=True)
        existing = cls.IFACELIST.read_text().split() if cls.IFACELIST.exists() else []
        all_ifaces = sorted(set(existing + ifaces))
        cls.IFACELIST.write_text(" ".join(all_ifaces))

    # ------------------------
    # eBPF load/query
    # ------------------------
    @classmethod
    def load_ebpf_program(cls, ifaces: List[str], bpf_prog: str, section: str,
                          direction: Literal["ingress","egress","both"]="both",
                          attach_type: Literal["tc","xdp"]="tc") -> None:
        """Load eBPF program on given interfaces."""
        if attach_type not in ("tc", "xdp"):
            raise ValueError("Invalid attach_type")
        for dev in ifaces:
            if attach_type == "tc":
                cls.ensure_clsact(dev)
                if direction in ("ingress", "both") and not cls.filter_present(dev, "ingress", bpf_prog):
                    cls.add_filter(dev, "ingress", bpf_prog, section)
                if direction in ("egress", "both") and not cls.filter_present(dev, "egress", bpf_prog):
                    cls.add_filter(dev, "egress", bpf_prog, section)
            else:
                cls.run_cmd(["ip", "link", "set", "dev", dev, "xdpgeneric", "obj", bpf_prog, "sec", section], check=True)
        cls.write_iface_list(ifaces)
        cls.LOGGER.info(f"Loaded eBPF on {ifaces}")

    @classmethod
    def query_loaded_programs(
        cls,
        iface: Optional[str] = None,
        attach_type: Optional[Literal["tc","xdp"]] = None,
        prog_name: Optional[str] = None
    ) -> List[LoadedProgram]:
        """Return a typed list of loaded programs with optional filtering."""
        result: List[LoadedProgram] = []
        try:
            interfaces = cls.get_dev_list_up()
        except Exception:
            interfaces = []

        for i in interfaces:
            if iface and i != iface:
                continue

            # TC filters
            if attach_type in (None, "tc"):
                for direction in ("ingress","egress"):
                    try:
                        cp = cls.run_cmd(["tc","filter","show","dev",i,direction], capture_output=True)
                        for line in cp.stdout.splitlines():
                            if "bpf" in line:
                                m = re.search(r"(\S+\.o):\[(\S+)\]", line)
                                if m:
                                    prog_file, section = m.groups()
                                    if prog_name and prog_name not in prog_file:
                                        continue
                                    result.append(LoadedProgram(
                                        interface=i,
                                        attach_type="tc",
                                        section=section,
                                        direction=direction,
                                        program=prog_file
                                    ))
                    except Exception:
                        continue

            # XDP programs
            if attach_type in (None, "xdp"):
                try:
                    cp = cls.run_cmd(["ip","-d","link","show",i], capture_output=True)
                    xdp_matches = re.findall(r"xdp\s+prog\s+id\s+\d+\s+name\s+(\S+)", cp.stdout)
                    for prog in xdp_matches:
                        if prog_name and prog_name not in prog:
                            continue
                        result.append(LoadedProgram(
                            interface=i,
                            attach_type="xdp",
                            section=None,
                            direction="-",
                            program=prog
                        ))
                except Exception:
                    continue

        return result
    # ------------------------
    # eBPF remove
    # ------------------------
    @classmethod
    def remove_ebpf_all_programs(cls) -> None:
        """
        Dangerous: removes all eBPF programs from all interfaces in IFACELIST.
        Deprecated: use remove_ebpf_program for strict removal by interface.
        """
        warnings.warn(
            "remove_ebpf_all_programs() is deprecated and dangerous. "
            "Use remove_ebpf_program() with explicit interfaces instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if cls.IFACELIST.exists():
            devs = cls.IFACELIST.read_text().split()
        else:
            devs = cls.get_dev_list_up()

        for dev in devs:
            cls.del_filters(dev)
            cls.run_cmd(["tc", "qdisc", "del", "dev", dev, "clsact"], check=False)

        cls.IFACELIST.unlink(missing_ok=True)
        cls.LOGGER.info("Removed all eBPF programs")

    @staticmethod
    def delete_bpf_filter(dev: str, direction: Literal["ingress","egress"], prog: str) -> bool:
        """
        Delete the TC filter that corresponds to the specific BPF program.
        Deletes by 'pref', which is kernel-safe.
        
        :param dev: interface name
        :param direction: 'ingress' or 'egress'
        :param prog: full path of BPF program
        :return: True if deleted, False otherwise
        """
        prog_name = os.path.basename(prog)
        cp = EBPFManager.run_cmd(
            ["tc", "filter", "show", "dev", dev, direction],
            capture_output=True,
            text=True,
            check=False
        )

        deleted = False
        for line in cp.stdout.splitlines():
            if prog_name in line:
                m = re.search(r"pref\s+(\d+)", line)
                if m:
                    pref = m.group(1)
                    EBPFManager.run_cmd(
                        ["tc", "filter", "del", "dev", dev, direction, "protocol", "all", "pref", pref, "bpf"],
                        check=False
                    )
                    deleted = True
        return deleted

    @classmethod
    def remove_ebpf_program(
        cls,
        bpf_prog: str,
        attach_type: Literal["tc","xdp"],
        direction: Literal["ingress","egress","both"],
        ifaces: List[str]
    ) -> None:
        """
        Strict removal of a specific eBPF program.
        
        Must provide attach_type, direction, and a list of interfaces.
        Does NOT fall back to IFACELIST. Only removes filters matching the program.
        
        :param bpf_prog: full path to BPF program
        :param attach_type: 'tc' or 'xdp'
        :param direction: 'ingress', 'egress' or 'both'
        :param ifaces: list of interfaces to remove program from
        """
        if not ifaces:
            raise ValueError("You must provide a list of interfaces for strict removal.")

        for dev in ifaces:
            if attach_type == "tc":
                if direction in ("ingress", "both"):
                    removed = cls.delete_bpf_filter(dev, "ingress", bpf_prog)
                    if removed:
                        cls.LOGGER.info(f"Removed ingress filter of '{bpf_prog}' from {dev}")
                    else:
                        cls.LOGGER.info(f"No ingress filter for '{bpf_prog}' on {dev}")

                if direction in ("egress", "both"):
                    removed = cls.delete_bpf_filter(dev, "egress", bpf_prog)
                    if removed:
                        cls.LOGGER.info(f"Removed egress filter of '{bpf_prog}' from {dev}")
                    else:
                        cls.LOGGER.info(f"No egress filter for '{bpf_prog}' on {dev}")

            elif attach_type == "xdp":
                cls.run_cmd(["ip", "link", "set", "dev", dev, "xdpgeneric", "off"], check=False)

            else:
                raise ValueError(f"Invalid attach_type: {attach_type}")

        cls.LOGGER.info(f"Strictly removed program '{bpf_prog}' from interfaces: {ifaces}")