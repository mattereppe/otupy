from otupy.types.base import Record

class AttachType(Record):
    """
    OpenC2-compliant record representing the eBPF attach type.
    Allowed values: "tc", "xdp"
    """

    Name: str  # public OpenC2 field
    VALID_ATTACH_TYPES = {"tc", "xdp","kprobe"}

    # ------------------------
    # Constructor
    # ------------------------
    def __init__(self, attach_type: str | None = None):
        super().__init__()
        self.Name = attach_type
        self.validate_fields()

    # ------------------------
    # Validation
    # ------------------------
    def validate_fields(self):
        if not self.Name:
            raise ValueError("AttachType cannot be None")
        if not isinstance(self.Name, str):
            raise TypeError(f"AttachType must be str, got {type(self.Name).__name__}")
        if self.Name.lower() not in self.VALID_ATTACH_TYPES:
            valid = ", ".join(self.VALID_ATTACH_TYPES)
            raise ValueError(f"Invalid attach type '{self.Name}'. Expected one of: {valid}")

    # ------------------------
    # Serialization
    # ------------------------
    def to_dict(self):
        return {"Name": self.Name}

    # ------------------------
    # Deserialization
    # ------------------------
    @classmethod
    def fromdict(cls, dic, encoder=None):
        """
        Build an AttachType instance from a dictionary.
        Used during Otupy deserialization.
        """
        if not isinstance(dic, dict):
            raise TypeError(f"Expected dict to build {cls.__name__}, got {type(dic).__name__}")

        name = dic.get("Name")
        return cls(attach_type=name)
