from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """Abstract base class for all file types."""

    def __init__(self, file, file_conf=None):
        self.file = file
        self.file_conf = file_conf

        self.results = []

    @abstractmethod
    def extract_bills(self):
        """Main entry point for Extractor"""
        pass
