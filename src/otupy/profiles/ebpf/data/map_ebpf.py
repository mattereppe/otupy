from __future__ import annotations
from otupy.types.base import Record


class MapeBPF(Record):
    """
    OpenC2-compliant record for an eBPF map.
    """

    Name: str
    Id: str

    def __init__(self, Name: str, Id: str):
        super().__init__()
        self.Name = Name
        self.Id = Id
        self.validate_fields()

    def validate_fields(self):
        if not isinstance(self.Name, str):
            raise TypeError("Map.Name must be str")

        if not isinstance(self.Id, str):
            raise TypeError("Map.Id must be str")