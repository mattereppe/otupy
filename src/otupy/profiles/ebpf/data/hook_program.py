from otupy.types.base import Record


class AttachType(Record):
    """
    OpenC2-compliant record representing the eBPF attach type.
    Allowed values: "tc", "xdp"
    """

    Name: str
    VALID_ATTACH_TYPES = {"tc", "xdp"}

    def __init__(self, Name: str):
        super().__init__()
        self.Name = Name
        self.validate_fields()

    def validate_fields(self):
        if not isinstance(self.Name, str):
            raise TypeError(f"AttachType.Name must be str, got {type(self.Name).__name__}")

        if self.Name.lower() not in self.VALID_ATTACH_TYPES:
            valid = ", ".join(self.VALID_ATTACH_TYPES)
            raise ValueError(f"Invalid AttachType '{self.Name}'. Expected one of: {valid}")