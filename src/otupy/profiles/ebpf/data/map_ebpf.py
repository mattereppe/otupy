from __future__ import annotations
from otupy.types.base import Record


class MapeBPF(Record):
    """
    OpenC2-compliant record for an eBPF map.
    """

    name: str
    id: str

    def __init__(self, name: str, id: str):
        super().__init__()
        self.name = name
        self.id = id
        self.validate_fields()

    def validate_fields(self):
        if not isinstance(self.name, str):
            raise TypeError("Map.Name must be str")

        if not isinstance(self.id, str):
            raise TypeError("Map.Id must be str")