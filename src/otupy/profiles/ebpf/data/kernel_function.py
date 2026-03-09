import os
from otupy.types.base import Record

class KernelFunction(Record):
    """
    Represents a kernel function to attach a kprobe to.
    """

    Name: str  # Kernel function symbol

    @classmethod
    def fromdict(cls, dic, encoder=None):
        if not isinstance(dic, dict):
            raise TypeError(f"Expected dict, got {type(dic).__name__}")
        name = dic.get("Name")
        return cls(Name=name)

    def __init__(self, Name: str, validate: bool = True):
        super().__init__()

        self.Name = Name.strip()
        if not self.Name:
            raise ValueError("Kernel function name cannot be empty")

        if validate:
            self.validate_exists()

    # Optional runtime validation
    def validate_exists(self):
        """
        Checks if the kernel symbol exists in /proc/kallsyms
        """
        if not os.path.exists("/proc/kallsyms"):
            return  # Cannot validate, maybe not Linux or no permissions

        found = False
        try:
            with open("/proc/kallsyms", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[2] == self.Name:
                        found = True
                        break
        except PermissionError:
            # Could be root-only, skip validation
            return

        if not found:
            raise ValueError(f"Kernel function '{self.Name}' not found in /proc/kallsyms")

    # Representation
    def __repr__(self):
        return f"KernelFunction(Name={self.Name})"

    def __str__(self):
        return self.Name

    # JSON/OpenC2 support
    def to_dict(self):
        return {"Name": self.Name}