from __future__ import annotations
from otupy.types.base import Record
import os
from typing import Optional, Union

from otupy.types.data.uri import URI

class ProgramFile(Record):
    """
    OpenC2-compliant record representing a source or compiled eBPF program file.
    Validates file type and ensures the eBPF section (SEC) is present.
    """

    VALID_EBPF_EXTENSIONS = {".c", ".o", ".bpf", ".ebpf"}

    # ------------------------
    # OpenC2 public fields
    # ------------------------
    Name: str
    isUri: bool = False
    Section: Optional[str]
    @classmethod
    def fromdict(cls, dic, encoder):
        """
        Build a ProgramFile instance from a dictionary.
        Used by Otupy deserialization.
        """
        if not isinstance(dic, dict):
            raise TypeError(f"Expected dict to build {cls.__name__}, got {type(dic).__name__}")

        name = dic.get("Name")
        section = dic.get("Section")
        return cls(Name=name, Section=section)

    def __init__(self, Name: Optional[str] = None, Section: Optional[str] = None, isUri: bool = False, Program: Optional[Union[str, "ProgramFile"]] = None, **kwargs):
        """
        Supports:
        - Name / Section (for deserialization)
        - Program + Section 
        """
        super().__init__()  # Must call first for OpenC2 Record

        # Legacy constructor with 'Program'
        if Program:
            self.Name = Program.strip()
            self.Section = Section
            self.isUri = isUri
        else:
            self.Name = Name
            self.Section = Section
            self.isUri = isUri

        # Validation and section detection
        self.validate_fields()
        if not self.Section:
            self.detect_section()

    # ------------------------
    # Validation
    # ------------------------
    def validate_fields(self):
        if not self.Name:
            raise ValueError("Program file name cannot be None or empty.")

        if not isinstance(self.Name, str):
            raise TypeError(f"Expected 'Name' to be str, got {type(self.Name).__name__}")

        _, ext = os.path.splitext(self.Name)
        if ext.lower() not in self.VALID_EBPF_EXTENSIONS:
            valid_list = ", ".join(self.VALID_EBPF_EXTENSIONS)
            raise ValueError(f"Invalid eBPF file extension '{ext}'. Expected one of: {valid_list}")

    # ------------------------
    # Section detection
    # ------------------------
    def detect_section(self):
        if self.Section:
            return  # already set

        _, ext = os.path.splitext(self.Name)

        if ext.lower() == ".c":
            # parse SEC("…") macro from source file
            try:
                with open(self.Name, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('SEC("') and line.endswith('")'):
                            self.Section = line[5:-2]
                            return
            except Exception as e:
                raise RuntimeError(f"Failed to read source file '{self.Name}': {e}")

        elif ext.lower() in {".o", ".bpf", ".ebpf"}:
            self.Section = None  # cannot auto-detect section in compiled files

        if not self.Section:
            raise ValueError(f"eBPF section (SEC) not found in file '{self.Name}'.")

    # ------------------------
    # Representation
    # ------------------------
    def __repr__(self):
        return f"ProgramFile(Name={self.Name}, Section={self.Section})"

    def __str__(self):
        return f"ProgramFile(Name={self.Name}, Section={self.Section})"

    # ------------------------
    # OpenC2 JSON support
    # ------------------------
    def to_dict(self):
        return {"Name": self.Name, "Section": self.Section}
