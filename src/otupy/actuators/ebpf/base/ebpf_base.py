from abc import ABC, abstractmethod
from typing import List

class BaseEBPFProgram(ABC):
    """
    Abstract base for any eBPF program type.
    """

    @abstractmethod
    def load(self, ifaces: List[str] = None) -> None:
        """Load the program into the kernel."""
        pass

    @abstractmethod
    def query(self) -> List[dict]:
        """Query loaded instances of this program."""
        pass

    @abstractmethod
    def remove(self, ifaces: List[str] = None) -> None:
        """Remove loaded instances."""
        pass