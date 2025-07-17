from abc import ABC, abstractmethod
from typing import List
from models.repository import RepositoryData

class BaseExporter(ABC):
    """Base class for data exporters"""
    
    def __init__(self, output_file: str):
        self.output_file = output_file
    
    @abstractmethod
    def export(self, repositories: List[RepositoryData]) -> None:
        """Exports the repository data"""
        pass
    
    def _get_file_extension(self) -> str:
        """Returns the file extension based on the exporter type"""
        return self.output_file.split('.')[-1] if '.' in self.output_file else ''