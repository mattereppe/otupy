from __future__ import annotations
from otupy.types.base import Record
import re
from typing import List, Optional, Union

class Interfaces(Record):
    """
    Represents a list of network interfaces for attaching eBPF programs.
    Validates interface names against Linux naming conventions.
    """

    # Regex pattern for valid Linux interface names (eth0, wlp3s0, enp0s31f6, etc.)
    IFACE_RE = re.compile(r"^[a-zA-Z0-9_.:-]+$")

    Names: List[str]

    def __init__(self, interfaces: Optional[Union[List[str], "Interfaces"]] = None):
        """
        Accepts:
        - List of interface names (strings)
        - Another Interfaces object (copy constructor)
        - None (empty list)
        """
        super().__init__()

        if isinstance(interfaces, Interfaces):
            self.Names = interfaces.Names.copy()
        elif isinstance(interfaces, list):
            self.Names = interfaces.copy()
        elif interfaces is None:
            self.Names = []
        else:
            raise TypeError(f"Expected list of strings or Interfaces, got {type(interfaces).__name__}")

        self.validate_fields()

    def validate_fields(self):
        """Validate each interface name."""
        if not isinstance(self.Names, list):
            raise TypeError(f"Expected 'Names' to be list, got {type(self.Names).__name__}")

        for iface in self.Names:
            if not isinstance(iface, str):
                raise TypeError(f"Interface name must be string, got {type(iface).__name__}")
            iface = iface.strip()
            if not iface:
                raise ValueError("Interface name cannot be empty or whitespace.")
            if not self.IFACE_RE.fullmatch(iface):
                raise ValueError(f"Invalid interface name: '{iface}'")

    def add(self, iface: str):
        """Add a new interface with validation."""
        if not isinstance(iface, str):
            raise TypeError(f"Interface must be string, got {type(iface).__name__}")
        iface = iface.strip()
        if not iface:
            raise ValueError("Interface name cannot be empty or whitespace.")
        if not self.IFACE_RE.fullmatch(iface):
            raise ValueError(f"Invalid interface name: '{iface}'")
        if iface not in self.Names:
            self.Names.append(iface)

    def remove(self, iface: str):
        """Remove an interface if it exists."""
        if iface in self.Names:
            self.Names.remove(iface)

    def __repr__(self):
        return f"Interfaces(Names={self.Names})"

    def __str__(self):
        return f"Interfaces: {', '.join(self.Names)}"
