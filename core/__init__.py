"""
COM v4 - Cognitive Architecture Core Module

This module contains the brain of the system: agent loop, context management,
and reflection capabilities that enable 1.5B models to perform at 7B+ levels.
"""

from .agent_loop import CognitiveAgent
from .context_manager import ContextManager
from .reflection_module import ReflectionEngine

__all__ = ["CognitiveAgent", "ContextManager", "ReflectionEngine"]
__version__ = "4.0.0"
