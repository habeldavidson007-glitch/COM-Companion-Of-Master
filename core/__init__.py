"""
COM IDE Core System - Foundation Module.

This module provides the core infrastructure for the COM IDE, including:
- Adaptive routing with RAM-aware model selection
- Schema-enforced LLM outputs via instructor
- Context compression and wiki retrieval
- Rule-first intent classification

Architecture: "Compiler-Lite" Pipeline
Flow: User Input → Signal Parser → Wiki Retrieval → LLM (JSON Plan) → Harness Execution
"""

from .signal_schema import (
    ValidateNodePath,
    ExplainError,
    RefactorSafe,
    SignalSchema,
)
from .context_compressor import compress_context
from .wiki_retriever import WikiRetriever
from .intent_router import IntentRouter
from .ram_monitor import get_available_ram_gb, can_load_model
from .adaptive_router import AdaptiveRouter

__version__ = "1.0.0"
__all__ = [
    "ValidateNodePath",
    "ExplainError",
    "RefactorSafe",
    "SignalSchema",
    "compress_context",
    "WikiRetriever",
    "IntentRouter",
    "get_available_ram_gb",
    "can_load_model",
    "AdaptiveRouter",
]
