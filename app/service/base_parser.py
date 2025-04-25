from abc import ABC, abstractmethod
from typing import Dict

class BaseParser(ABC):
    """Defines the interface for both local and remote TTY parsers."""

    @abstractmethod
    def parse_tty_message(
            self,
            message: str,
    ) -> Dict:
        pass