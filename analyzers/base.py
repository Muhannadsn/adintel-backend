from abc import ABC, abstractmethod
from models.ad_creative import Analysis, Screenshot

class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze_screenshot(self, screenshot: Screenshot) -> Analysis:
        """Analyzes a screenshot and returns an Analysis object."""
        pass
