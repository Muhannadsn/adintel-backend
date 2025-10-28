from abc import ABC, abstractmethod
from models.ad_creative import Screenshot, Creative

class BaseExtractor(ABC):
    @abstractmethod
    def extract_creative(self, creative: Creative) -> Screenshot:
        """Extracts a creative and returns a Screenshot object."""
        pass
