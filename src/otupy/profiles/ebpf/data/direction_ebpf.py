from __future__ import annotations
from otupy.types.base import Record

class Direction(Record):
    """
    OpenC2-compliant record for packet direction in eBPF (TC/XDP).
    Allowed values: "ingress", "egress", "both"
    """

    # ------------------------
    # OpenC2 field definition
    # ------------------------
    Name: str
    VALID_DIRECTIONS = {"ingress", "egress", "both"}

    def __init__(self, direction: str | None = None):
        super().__init__()
        self.Name = direction
        self.validate_fields()

    # ------------------------
    # Validation
    # ------------------------
    def validate_fields(self):
        if not self.Name or self.Name.lower() not in self.VALID_DIRECTIONS:
            valid = ", ".join(self.VALID_DIRECTIONS)
            raise ValueError(f"Invalid direction '{self.Name}'. Expected one of: {valid}")

    # ------------------------
    # Serialization for JSON / OpenC2
    # ------------------------
    def to_dict(self):
        return {"Name": self.Name}

    # ------------------------
    # Deserialization from dictionary
    # ------------------------
    @classmethod
    def fromdict(cls, dic, encoder=None):
        """
        Build a Direction instance from a dictionary.
        Used during Otupy deserialization.
        """
        if not isinstance(dic, dict):
            raise TypeError(f"Expected dict to build {cls.__name__}, got {type(dic).__name__}")
        
        name = dic.get("Name")
        return cls(direction=name)
