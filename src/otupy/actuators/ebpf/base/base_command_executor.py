from abc import ABC, abstractmethod
from typing import List, Union

class BaseCommandExecutor(ABC):
    @abstractmethod
    def run_cmd(self, cmd: Union[str, List[str]], check: bool = True, capture_output: bool = True):
        """Run a command safely. Must be implemented per executor type."""
        pass