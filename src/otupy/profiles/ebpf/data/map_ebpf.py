from __future__ import annotations
from otupy.types.base import Record

class MapeBPF(Record):
    """
    OpenC2-compliant record for map defined in a eBPF program.
    
    """
    Name: str
    Id: str
    def __init__(self, name: str, id: str):
        super().__init__()
        self.Name = name
        self.Id = id
    def to_dict(self):
        return {"Name": self.Name, "Id": self.Id}
    
    @classmethod
    def fromdict(cls, dic, encoder=None):
        """
        Build a MapeBPF instance from a dictionary.
        Used during Otupy deserialization.
        """
        if not isinstance(dic, dict):
            raise TypeError(f"Expected dict to build {cls.__name__}, got {type(dic).__name__}")
        
        name = dic.get("Name")
        id = dic.get("Id")
        return cls(name=name, id=id)