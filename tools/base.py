"""
Base Module Interface for COM (Companion Of Master)
All skill modules must inherit from this class to ensure compatibility.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseTool(ABC):
    """Abstract base class for all COM tools/modules."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = "No description provided."
        self.enabled = True
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool's main functionality.
        Must be implemented by each specific tool.
        
        Args:
            **kwargs: Dynamic arguments based on tool requirements
            
        Returns:
            Any: Result of the operation (string, dict, list, etc.)
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about this tool for the AI to understand its capabilities."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled
        }
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input arguments before execution.
        Override in child classes for specific validation logic.
        """
        return True
