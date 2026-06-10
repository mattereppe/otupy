from __future__ import annotations
from otupy.types.base import Record
import os


class ProgramFile(Record):
    """
    OpenC2-compliant record representing an eBPF program file.
    """

    VALID_EXTENSIONS = {".c", ".o", ".bpf", ".ebpf"}

    file_name: str
    file_path: str
    section: str
    is_uri: bool = False

    def __init__(
        self,
        file_name: str,
        file_path: str,
        section: str,
        is_uri: bool = False
    ):
        super().__init__()

        self.file_name = file_name
        self.file_path = file_path
        self.section = section
        self.is_uri = is_uri

        self.validate_fields()

    def validate_fields(self):
        if not isinstance(self.file_name, str) or not self.file_name:
            raise ValueError("ProgramFile.file_name must be a non-empty string")

        if not isinstance(self.file_path, str) or not self.file_path:
            raise ValueError("ProgramFile.file_path must be a non-empty string")

        if not isinstance(self.section, str) or not self.section:
            raise ValueError("ProgramFile.section must be a non-empty string")

        _, ext = os.path.splitext(self.file_name)

        if ext.lower() not in self.VALID_EXTENSIONS:
            valid = ", ".join(self.VALID_EXTENSIONS)
            raise ValueError(f"Invalid eBPF file extension '{ext}'. Expected: {valid}")