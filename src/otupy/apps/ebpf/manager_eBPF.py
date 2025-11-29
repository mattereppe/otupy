#!/usr/bin/env python3
"""
EBPFManager — Flexible Python eBPF API

Features:
- Load/unload multiple eBPF programs (local or remote)
- Attach to tc clsact (ingress/egress) or XDP
- Start/stop user-space utilities with structured options
- Inspect attached programs
- Remove pinned maps and cleanup
"""

from __future__ import annotations
import os
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Optional
import requests

class EBPFManager:
    #RUNDIR → ensures a place to store runtime files.

    #PIDFILE → tracks the running user-space process.

    #IFACELIST → tracks which interfaces have eBPF programs attached.
    
    def __init__(self, rundir: str = "/var/run/ebpfmanager", pidfile: Optional[str] = None):
        self.RUNDIR = Path(rundir)
        self.RUNDIR.mkdir(parents=True, exist_ok=True)
        self.PIDFILE = Path(pidfile) if pidfile else self.RUNDIR / "userland.pid"
        self.IFACELIST = self.RUNDIR / "iface.list"

    # -----------------------------
    # Helper: run shell commands
    # -----------------------------
    @staticmethod
    def run_cmd(cmd, check=False, capture_output=False, text=True):
        if isinstance(cmd, (list, tuple)):
            args = cmd
        else:
            args = shlex.split(cmd)
        return subprocess.run(args, check=check, capture_output=capture_output, text=text)

    # -----------------------------
    # Fetch remote programs
    # -----------------------------
    @staticmethod
    def fetch_remote_program(url: str, dest: str) -> str:
        """Download remote eBPF program and return local path."""
        r = requests.get(url)
        r.raise_for_status()
        path = Path(dest)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(r.content)
        return str(path.resolve())

    # -----------------------------
    # Interfaces / Qdisc / Filters
    # -----------------------------
    @staticmethod
    def get_dev_list_up() -> List[str]:
        cp = EBPFManager.run_cmd("ip -o l show up", capture_output=True)
        return [line.split(": ")[1].split()[0] for line in cp.stdout.strip().splitlines()]

    @staticmethod
    def ensure_clsact(dev: str):
        cp = EBPFManager.run_cmd(f"tc qdisc show dev {dev} handle ffff:", capture_output=True)
        if "clsact" not in cp.stdout:
            EBPFManager.run_cmd(f"tc qdisc add dev {dev} clsact", check=True)

    @staticmethod
    def filter_present(dev: str, direction: str, prog: str) -> bool:
        cp = EBPFManager.run_cmd(f"tc filter show dev {dev} {direction}", capture_output=True)
        return prog in cp.stdout

    @staticmethod
    def add_filter(dev: str, direction: str, bpf_prog: str, section: str):
        cmd = ["tc", "filter", "add", "dev", dev, direction, "bpf", "da", "obj", bpf_prog, "sec", section]
        EBPFManager.run_cmd(cmd, check=True)

    @staticmethod
    def del_filters(dev: str):
        for d in ("ingress","egress"):
            try:
                EBPFManager.run_cmd(["tc","filter","del","dev",dev,d], check=False)
            except Exception:
                pass

    def write_iface_list(self, ifaces: List[str]):
        self.RUNDIR.mkdir(parents=True, exist_ok=True)
        with open(self.IFACELIST, "w") as f:
            f.write(" ".join(ifaces))

    # -----------------------------
    # eBPF Program management
    # -----------------------------
    def load_ebpf_program(self,
                          ifaces: List[str],
                          bpf_prog: str,
                          section: str,
                          direction: str = "both",
                          attach_type: str = "tc"):
        """
        Load a BPF program on specified interfaces.
        attach_type: 'tc' (clsact) or 'xdp'
        """
        if attach_type not in ("tc", "xdp"):
            raise ValueError(f"Unsupported attach_type: {attach_type}")

        for dev in ifaces:
            if attach_type == "tc":
                self.ensure_clsact(dev)
                if direction in ("ingress","both") and not self.filter_present(dev, "ingress", bpf_prog):
                    self.add_filter(dev, "ingress", bpf_prog, section)
                if direction in ("egress","both") and not self.filter_present(dev, "egress", bpf_prog):
                    self.add_filter(dev, "egress", bpf_prog, section)
            elif attach_type == "xdp":
                cmd = ["ip", "link", "set", "dev", dev, "xdpgeneric", "obj", bpf_prog, "sec", section]
                self.run_cmd(cmd, check=True)

        self.write_iface_list(ifaces)

    def remove_ebpf_programs(self):
        """Remove BPF programs from interfaces in iface list or all up interfaces."""
        if self.IFACELIST.exists():
            with open(self.IFACELIST, "r") as f:
                devs = f.read().strip().split()
        else:
            devs = self.get_dev_list_up()
        for dev in devs:
            self.del_filters(dev)
            # Attempt to remove clsact qdisc
            try:
                self.run_cmd(["tc","qdisc","del","dev",dev,"clsact"], check=False)
            except Exception:
                pass
        self.IFACELIST.unlink(missing_ok=True)

    # -----------------------------
    # User-space management
    # -----------------------------
    def start_userland(self, userland_path: str, options: dict = None, logfile: str = None):
        """
        Start a user-space program with structured options.
        options: dict of argument_name -> value
        """
        if not Path(userland_path).exists() or not os.access(userland_path, os.X_OK):
            raise FileNotFoundError(f"Userland utility not found or not executable: {userland_path}")
        if self.PIDFILE.exists():
            pid = int(self.PIDFILE.read_text().strip())
            try:
                os.kill(pid, 0)
                print(f"Userland process already running (PID {pid})")
                return
            except Exception:
                self.PIDFILE.unlink()

        # Build command
        cmd = [userland_path]
        if options:
            for k, v in options.items():
                if isinstance(v, bool):
                    if v:
                        cmd.append(f"--{k}")
                else:
                    cmd.extend([f"--{k}", str(v)])
        logfile_path = Path(logfile or self.RUNDIR / "userland.log")
        logfile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(logfile_path, "a+") as logf:
            proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, start_new_session=True)
        with open(self.PIDFILE, "w") as f:
            f.write(str(proc.pid))
        print(f"Started {userland_path} (PID {proc.pid}), logs -> {logfile_path}")

    def stop_userland(self):
        if not self.PIDFILE.exists():
            print("Userland process not running")
            return
        pid = int(self.PIDFILE.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            self.PIDFILE.unlink()
            return
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                break
        else:
            os.kill(pid, signal.SIGKILL)
        self.PIDFILE.unlink()
        print(f"Stopped userland process {pid}")

    # -----------------------------
    # Pinned BPF maps
    # -----------------------------
    @staticmethod
    def remove_pinned_map(path: str):
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed pinned map {path}")

    # -----------------------------
    # Inspect loaded programs
    # -----------------------------
    @staticmethod
    def list_tc_filters(dev: str):
        cp = EBPFManager.run_cmd(["tc","filter","show","dev",dev], capture_output=True)
        return cp.stdout.strip()

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    manager = EBPFManager()
    interfaces = ["wlp7s0"]
    bpf_program = "./src/otupy/apps/ebpf/allow_all.o" 
    full_path_bpf_program = os.path.abspath(bpf_program)
    section = "main" # this is the section in respective file .c --> in this allow_all.c
    # Load eBPF program (tc ingress+egress)
    manager.load_ebpf_program(interfaces, full_path_bpf_program, section, direction="both", attach_type="tc")
    print("eBPF program loaded successfully!")

    # Start user-space utility
    #manager.start_userland("/usr/local/bin/userland_program",
    #                       options={"interval": 10, "dumpdir": "/tmp", "json": True})

    # List attached filters
    for iface in interfaces:
        print(manager.list_tc_filters(iface))

    # Stop user-space and remove programs
    manager.stop_userland()
    manager.remove_ebpf_programs()
    print("Cleanup complete.")
