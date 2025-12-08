#!/usr/bin/env python3
"""
Fully Static eBPF Manager
- Structured logging
- Runtime type checking
- Async support
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
from typing import List, Optional, Callable, Any, Dict
import requests
import inspect
from functools import wraps
from typing import get_origin, get_args, Union, Any

class JSONFormatter(logging.Formatter):
    """Simple JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        return json.dumps(log_record)
# ===========================================================
# Runtime type checking 
# has been added to improve safety and limits crash and bugs
# stopping the program at runtime
# maybe can be avoided during production since it has light 
# overhead, decreasing the performance 
# ===========================================================
def check_type(value, expected):
    """Safely check if value matches expected type annotation."""
    if expected in (Any, None):
        return True

    origin = get_origin(expected)
    args = get_args(expected)

    # Optional[T] is Union[T, NoneType]
    if origin is Union:
        return any(check_type(value, arg) for arg in args)

    # Normal type
    if isinstance(expected, type):
        return isinstance(value, expected)

    # Fallback (cannot check generics like list[int])
    return True

def runtime_type_check(func: Callable) -> Callable:
    """Runtime argument + return type checking."""
    sig = inspect.signature(func)
    annotations = func.__annotations__

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        # Check parameter types
        for name, value in bound.arguments.items():
            if name in annotations:
                expected = annotations[name]
                if (
                    expected is not None
                    and not isinstance(expected, type)
                    and expected != Any
                ):
                    continue
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


# ===========================================================
# Structured Logging
# ===========================================================

def setup_logger(logfile: Path, json_logs: bool = False, level=logging.DEBUG):
    """Setup logger with optional JSON output"""
    logfile.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("EBPFManager")
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Formatter
    if json_logs:
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                import json
                log_record = {
                    "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }
                return json.dumps(log_record)
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # File handler
    file_handler = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (plain text)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(console)

    return logger


# ===========================================================
# EBPFManager (Fully Static)
# ===========================================================
class EBPFManager:
    """
    Fully static eBPF manager with:
    - static configuration
    - static methods
    - structured logging
    - async support
    """

    RUNDIR: Path = Path("/var/run/ebpfmanager")
    PIDFILE: Path = RUNDIR / "userland.pid"
    IFACELIST: Path = RUNDIR / "iface.list"
    LOGGER: logging.Logger = setup_logger(RUNDIR / "ebpfmanager.log")

    # -------------------------------------------------------
    # Initialization
    # -------------------------------------------------------
    @classmethod
    @runtime_type_check
    def init(
        cls,
        rundir: str = "/var/run/ebpfmanager",
        pidfile: Optional[str] = None,
        log_level: int = logging.INFO,
        json_logs: bool = False
    ) -> None:
        cls.RUNDIR = Path(rundir)
        cls.RUNDIR.mkdir(parents=True, exist_ok=True)

        cls.PIDFILE = Path(pidfile) if pidfile else cls.RUNDIR / "userland.pid"
        cls.IFACELIST = cls.RUNDIR / "iface.list"

        # Setup logger with optional JSON output
        cls.LOGGER = setup_logger(
            logfile=cls.RUNDIR / "ebpfmanager.log",
            level=log_level,
            json_logs=json_logs
        )

        cls.LOGGER.info(f"EBPFManager initialized at {cls.RUNDIR}")

    # -------------------------------------------------------
    # Security Validation
    # -------------------------------------------------------
    @staticmethod
    def secure_validate_token(token: str, allow_abs: bool = True):
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
        if not isinstance(args, (list, tuple)):
            raise TypeError("Command must be list/tuple")

        for token in args:
            EBPFManager.secure_validate_token(token)

        return list(args)

    # -------------------------------------------------------
    # Sync command runner
    # -------------------------------------------------------
    @staticmethod
    @runtime_type_check
    def run_cmd(cmd: Any, check: bool = False,
                capture_output: bool = False, text: bool = True):
        if isinstance(cmd, (list, tuple)):
            args = list(cmd)
        else:
            args = shlex.split(cmd)

        args = EBPFManager.secure_middleware(args)

        EBPFManager.LOGGER.debug(f"Running command: {args}")

        return subprocess.run(
            args,
            check=check,
            capture_output=capture_output,
            text=text
        )

    # -------------------------------------------------------
    # ASYNC command runner
    # -------------------------------------------------------
    @staticmethod
    async def run_cmd_async(cmd: Any,
                            capture_output: bool = True,
                            text: bool = True):
        if isinstance(cmd, (list, tuple)):
            args = list(cmd)
        else:
            args = shlex.split(cmd)

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

    # -------------------------------------------------------
    # Interface helpers
    # -------------------------------------------------------
    @staticmethod
    def get_dev_list_up() -> List[str]:
        cp = EBPFManager.run_cmd("ip -o l show up", capture_output=True)
        return [line.split(": ")[1].split()[0] for line in cp.stdout.splitlines()]

    @staticmethod
    def ensure_clsact(dev: str):
        cp = EBPFManager.run_cmd(f"tc qdisc show dev {dev} handle ffff:",
                                 capture_output=True)
        if "clsact" not in cp.stdout:
            EBPFManager.run_cmd(f"tc qdisc add dev {dev} clsact", check=True)

    @staticmethod
    def filter_present(dev: str, direction: str, prog: str) -> bool:
        cp = EBPFManager.run_cmd(f"tc filter show dev {dev} {direction}",
                                 capture_output=True)
        return prog in cp.stdout

    @staticmethod
    def add_filter(dev: str, direction: str, prog: str, section: str):
        EBPFManager.run_cmd([
            "tc", "filter", "add", "dev", dev, direction,
            "bpf", "da", "obj", prog, "sec", section
        ], check=True)

    @staticmethod
    def del_filters(dev: str):
        for d in ("ingress", "egress"):
            EBPFManager.run_cmd(
                ["tc", "filter", "del", "dev", dev, d], check=False
            )

    # -------------------------------------------------------
    # Save iface list
    # -------------------------------------------------------
    @classmethod
    def write_iface_list(cls, ifaces: List[str]):
        cls.IFACELIST.write_text(" ".join(ifaces))

    # -------------------------------------------------------
    # Load eBPF (sync)
    # -------------------------------------------------------
    @classmethod
    def load_ebpf_program(cls, ifaces: List[str], bpf_prog: str,
                          section: str, direction: str = "both",
                          attach_type: str = "tc"):
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
                cls.run_cmd(["ip", "link", "set", "dev", dev, "xdpgeneric",
                             "obj", bpf_prog, "sec", section], check=True)

        cls.write_iface_list(ifaces)
        cls.LOGGER.info(f"Loaded eBPF on {ifaces}")

    # -------------------------------------------------------
    # Async load eBPF
    # -------------------------------------------------------
    @classmethod
    async def load_ebpf_program_async(cls, ifaces: List[str], bpf_prog: str,
                                      section: str, direction: str = "both",
                                      attach_type: str = "tc"):
        for dev in ifaces:
            if attach_type == "tc":
                cls.ensure_clsact(dev)
                if direction in ("ingress", "both") and not cls.filter_present(dev, "ingress", bpf_prog):
                    await cls.run_cmd_async(
                        ["tc", "filter", "add", "dev", dev, "ingress",
                         "bpf", "da", "obj", bpf_prog, "sec", section]
                    )
                if direction in ("egress", "both") and not cls.filter_present(dev, "egress", bpf_prog):
                    await cls.run_cmd_async(
                        ["tc", "filter", "add", "dev", dev, "egress",
                         "bpf", "da", "obj", bpf_prog, "sec", section]
                    )

            else:  # XDP
                await cls.run_cmd_async(
                    ["ip", "link", "set", "dev", dev, "xdpgeneric",
                     "obj", bpf_prog, "sec", section]
                )

        cls.write_iface_list(ifaces)
        cls.LOGGER.info("[async] eBPF loaded")

    # -------------------------------------------------------
    # Remove eBPF
    # -------------------------------------------------------
    @classmethod
    def remove_ebpf_programs(cls):
        if cls.IFACELIST.exists():
            devs = cls.IFACELIST.read_text().split()
        else:
            devs = cls.get_dev_list_up()

        for dev in devs:
            cls.del_filters(dev)
            cls.run_cmd(["tc", "qdisc", "del", "dev", dev, "clsact"],
                        check=False)

        cls.IFACELIST.unlink(missing_ok=True)
        cls.LOGGER.info("Removed all eBPF programs")

    # -------------------------------------------------------
    # Userland process management
    # -------------------------------------------------------
    @classmethod
    def start_userland(cls, path: str, options: Dict[str, Any] = None,
                       logfile: Optional[str] = None):
        path = Path(path)
        if not path.exists() or not os.access(path, os.X_OK):
            raise FileNotFoundError("Userland not executable")

        if cls.PIDFILE.exists():
            pid = int(cls.PIDFILE.read_text())
            try:
                os.kill(pid, 0)
                cls.LOGGER.warning(f"Userland already running pid={pid}")
                return
            except:
                cls.PIDFILE.unlink()

        cmd = [str(path)]
        if options:
            for k, v in options.items():
                if isinstance(v, bool):
                    if v:
                        cmd.append(f"--{k}")
                else:
                    cmd.extend([f"--{k}", str(v)])

        logfile_path = Path(logfile or cls.RUNDIR / "userland.log")
        logfile_path.parent.mkdir(parents=True, exist_ok=True)

        with open(logfile_path, "a+") as log:
            proc = subprocess.Popen(cmd, stdout=log,
                                    stderr=log, start_new_session=True)

        cls.PIDFILE.write_text(str(proc.pid))
        cls.LOGGER.info(f"Userland started pid={proc.pid}")

    @classmethod
    def stop_userland(cls):
        if not cls.PIDFILE.exists():
            cls.LOGGER.info("Userland not running")
            return

        pid = int(cls.PIDFILE.read_text())
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            cls.PIDFILE.unlink()
            return

        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                break
        else:
            os.kill(pid, signal.SIGKILL)

        cls.PIDFILE.unlink()
        cls.LOGGER.info(f"Userland stopped pid={pid}")

    # -------------------------------------------------------
    # Pinned Map Removal
    # -------------------------------------------------------
    @staticmethod
    def remove_pinned_map(path: str):
        if os.path.exists(path):
            os.remove(path)
            EBPFManager.LOGGER.info(f"Removed pinned map {path}")

    # -------------------------------------------------------
    # List TC filters
    # -------------------------------------------------------
    @staticmethod
    def list_tc_filters(dev: str) -> str:
        cp = EBPFManager.run_cmd(
            ["tc", "filter", "show", "dev", dev],
            capture_output=True
        )
        return cp.stdout.strip()
    
    @staticmethod
    def query_loaded_programs(
        iface: Optional[str] = None,
        attach_type: Optional[str] = None,
        prog_name: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Return a list of loaded programs with optional filtering by
        interface, attach type, or program name.

        :param iface: filter by interface name
        :param attach_type: 'tc' or 'xdp'
        :param prog_name: substring of program filename or section
        """
        result = []
        try:
            interfaces = EBPFManager.get_dev_list_up()
        except Exception:
            interfaces = []

        for i in interfaces:
            if iface and i != iface:
                continue  # skip non-matching interface

            # ----- TC filters -----
            if attach_type in (None, "tc"):
                for direction in ("ingress", "egress"):
                    try:
                        cp = EBPFManager.run_cmd(
                            ["tc", "filter", "show", "dev", i, direction],
                            capture_output=True
                        )
                        lines = cp.stdout.strip().splitlines()
                        for line in lines:
                            if "bpf" in line:
                                m = re.search(r"(\S+\.o):\[(\S+)\]", line)
                                if m:
                                    prog_file, section = m.groups()
                                    # TODO ADD SECTION FILE TO HAVE MORE ACCURACY
                                    program_full = f"{prog_file} [{section}]"
                                    if prog_name and prog_name not in program_full:
                                        continue
                                    result.append({
                                        "interface": i,
                                        "attach_type": "tc",
                                        "section": section,
                                        "direction": direction,
                                        "program": prog_file
                                    })
                    except Exception:
                        pass

            # ----- XDP programs -----
            if attach_type in (None, "xdp"):
                try:
                    cp = EBPFManager.run_cmd(
                        ["ip", "-d", "link", "show", i],
                        capture_output=True
                    )
                    xdp_matches = re.findall(r"xdp\s+prog\s+id\s+\d+\s+name\s+(\S+)", cp.stdout)
                    for prog in xdp_matches:
                        if prog_name and prog_name not in prog:
                            continue
                        result.append({
                            "interface": i,
                            "attach_type": "xdp",
                            "direction": "-",
                            "program": prog
                        })
                except Exception:
                    pass

        return result


"""


if __name__ == "__main__":
    # Initialize with logging and runtime type checks disabled by default
    EBPFManager.init(
        rundir="/tmp/ebpfmgr",
        json_logs=False,
        runtime_type_checks=False,
        log_level=logging.DEBUG,
    )

    # Sync example
    try:
        EBPFManager.load_ebpf_program(
            ifaces=["lo"],  # use a safe interface for example
            bpf_prog="/path/to/prog.o",
            section="main",
            direction="both",
            attach_type="tc",
        )
    except Exception as e:
        EBPFManager._log(logging.ERROR, "Sync load failed (expected in example)", exc=str(e))

    # Async example
    async def async_flow():
        try:
            await EBPFManager.load_ebpf_program_async(
                ifaces=["lo"],
                bpf_prog="/path/to/prog.o",
                section="main",
                direction="both",
                attach_type="tc",
            )
        except Exception as e:
            EBPFManager._log(logging.ERROR, "Async load failed (expected in example)", exc=str(e))

    asyncio.run(async_flow())
"""
