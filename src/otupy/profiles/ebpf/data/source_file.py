from __future__ import annotations
from otupy.types.base import Record
import os


class ProgramFile(Record):
    """
    OpenC2-compliant record representing an eBPF program file.
    """

    VALID_EXTENSIONS = {".c", ".o", ".bpf", ".ebpf"}

    FileName: str
    FilePath: str
    Section: str
    IsUri: bool = False

    def __init__(
        self,
        FileName: str,
        FilePath: str,
        Section: str,
        IsUri: bool = False
    ):
        super().__init__()

        self.FileName = FileName
        self.FilePath = FilePath
        self.Section = Section
        self.IsUri = IsUri

        self.validate_fields()

    def validate_fields(self):
        if not isinstance(self.FileName, str) or not self.FileName:
            raise ValueError("ProgramFile.FileName must be a non-empty string")

        if not isinstance(self.FilePath, str) or not self.FilePath:
            raise ValueError("ProgramFile.FilePath must be a non-empty string")

        if not isinstance(self.Section, str) or not self.Section:
            raise ValueError("ProgramFile.Section must be a non-empty string")

        _, ext = os.path.splitext(self.FileName)

        if ext.lower() not in self.VALID_EXTENSIONS:
            valid = ", ".join(self.VALID_EXTENSIONS)
            raise ValueError(f"Invalid eBPF file extension '{ext}'. Expected: {valid}")