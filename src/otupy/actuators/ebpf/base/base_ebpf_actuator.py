from otupy import Command, Response, StatusCode
from abc import ABC, abstractmethod
from typing import Optional

class BaseEBPFActuator(ABC):
    """Common interface for eBPF actuators."""
    
    @abstractmethod
    def create(self, cmd: Command) -> Response:
        pass

    @abstractmethod
    def query(self, cmd: Command) -> Response:
        pass

    @abstractmethod
    def delete(self, cmd: Command) -> Response:
        pass

    @abstractmethod
    def __is_addressed_to_actuator(self, actuator) -> bool:
        pass