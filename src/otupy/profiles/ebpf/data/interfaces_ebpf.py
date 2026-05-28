from __future__ import annotations
from otupy.types.base import Record
import re


class Interfaces(Record):
    """
    Represents a list of network interfaces for attaching eBPF programs.
    """

    IFACE_PATTERN = re.compile(r"^[a-zA-Z0-9_.:-]+$")

    iface: str

    def __init__(self, iface: str):
        super().__init__()
        self.iface = iface
        self.validate_fields()

    def validate_fields(self):
        if not isinstance(self.iface, str):
            raise TypeError("Interfaces.Names must be a str")
        if not self.IFACE_PATTERN.match(self.iface):
                raise ValueError(f"Invalid interface name: {self.iface}")


            