from __future__ import annotations
from otupy.types.base import Record


class Direction(Record):
    """
    OpenC2-compliant record for packet direction in eBPF (TC/XDP).
    Allowed values: "ingress", "egress", "both"
    """

    Name: str
    VALID_DIRECTIONS = {"ingress", "egress", "both"}

    def __init__(self, Name: str):
        super().__init__()
        self.Name = Name
        self.validate_fields()

    def validate_fields(self):
        if not isinstance(self.Name, str):
            raise ValueError("Direction.Name must be a string")

        if self.Name.lower() not in self.VALID_DIRECTIONS:
            valid = ", ".join(self.VALID_DIRECTIONS)
            raise ValueError(
                f"Invalid direction '{self.Name}'. Expected one of: {valid}"
            )