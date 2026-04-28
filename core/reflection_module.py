"""
COM v4 - Reflection Engine

Advanced self-verification module for deep error analysis.
This module provides structured reflection capabilities that enable
the model to catch and correct its own mistakes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum, auto

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of errors encountered during execution."""
    TOOL_EXECUTION = auto()
    LOGICAL_INCONSISTENCY = auto()
    LOW_CONFIDENCE = auto()
    CONTEXT_MISMATCH = auto()
    FORMAT_VIOLATION = auto()
    UNKNOWN = auto()


@dataclass
class ReflectionResult:
    """Result of a reflection analysis."""
    error_type: ErrorType
    root_cause: str
    suggested_fix: str
    confidence_adjustment: float
    should_retry: bool
    alternative_approaches: list[str]


class ReflectionEngine:
    """
    Specialized engine for analyzing errors and generating corrections.
    
    Unlike simple error handling, this engine forces structured analysis:
    1. Classify the error type
    2. Identify root cause
    3. Generate multiple alternative approaches
    4. Adjust confidence based on analysis
    5. Decide whether retry is worthwhile
    
    This meta-cognitive capability is what separates COM v4 from
    standard agent implementations.
    """
    
    def __init__(self, max_alternatives: int = 3):
        """
        Initialize the reflection engine.
        
        Args:
            max_alternatives: Maximum number of alternative approaches to generate
        """
        self.max_alternatives = max_alternatives
        self._reflection_history: list[ReflectionResult] = []
    
    def classify_error(self, error_message: str, context: dict[str, Any]) -> ErrorType:
        """
        Classify an error based on its characteristics.
        
        Args:
            error_message: The error string from the tool or model
            context: Additional context about when the error occurred
            
        Returns:
            ErrorType enumeration value
        """
        error_lower = error_message.lower()
        
        # Tool execution errors
        if any(kw in error_lower for kw in ["traceback", "exception", "failed"]):
            return ErrorType.TOOL_EXECUTION
        
        # Logical issues
        if any(kw in error_lower for kw in ["contradiction", "inconsistent", "invalid"]):
            return ErrorType.LOGICAL_INCONSISTENCY
        
        # Confidence-related
        if "low confidence" in error_lower or "uncertain" in error_lower:
            return ErrorType.LOW_CONFIDENCE
        
        # Context issues
        if any(kw in error_lower for kw in ["context", "memory", "history"]):
            return ErrorType.CONTEXT_MISMATCH
        
        # Format issues
        if any(kw in error_lower for kw in ["parse", "format", "json", "schema"]):
            return ErrorType.FORMAT_VIOLATION
        
        return ErrorType.UNKNOWN
    
    def analyze(
        self,
        thought: str,
        action: Optional[str],
        observation: Optional[str],
        error: Optional[str],
        confidence: float
    ) -> ReflectionResult:
        """
        Perform comprehensive reflection analysis.
        
        Args:
            thought: The original thought/reasoning
            action: The action taken (if any)
            observation: What was observed (if anything)
            error: Error message (if any)
            confidence: Original confidence score
            
        Returns:
            ReflectionResult with analysis and recommendations
        """
        # Determine error type
        if error:
            error_type = self.classify_error(error, {
                "thought": thought,
                "action": action,
                "observation": observation
            })
            root_cause = self._identify_root_cause(error, thought, action)
        else:
            # Low confidence reflection
            error_type = ErrorType.LOW_CONFIDENCE
            root_cause = self._identify_uncertainty_source(thought, confidence)
        
        # Generate suggested fix
        suggested_fix = self._generate_fix(error_type, root_cause, action)
        
        # Generate alternative approaches
        alternatives = self._generate_alternatives(error_type, thought, action)
        
        # Calculate confidence adjustment
        confidence_adjustment = self._calculate_confidence_adjustment(
            error_type, confidence, error
        )
        
        # Decide on retry
        should_retry = self._should_retry(error_type, confidence, len(alternatives))
        
        result = ReflectionResult(
            error_type=error_type,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            confidence_adjustment=confidence_adjustment,
            should_retry=should_retry,
            alternative_approaches=alternatives[:self.max_alternatives]
        )
        
        self._reflection_history.append(result)
        logger.info(f"Reflection completed: {error_type.name}, retry={should_retry}")
        
        return result
    
    def _identify_root_cause(
        self,
        error: str,
        thought: str,
        action: Optional[str]
    ) -> str:
        """Identify the fundamental cause of an error."""
        # Analyze the error pattern
        if "ZeroDivisionError" in error:
            return "Division by zero attempted - mathematical impossibility"
        elif "FileNotFoundError" in error:
            return "Requested file does not exist at specified path"
        elif "KeyError" in error:
            return "Attempted to access non-existent dictionary key"
        elif "JSONDecodeError" in error:
            return "Invalid JSON format in tool response or request"
        elif "timeout" in error.lower():
            return "Operation exceeded time limit"
        else:
            return f"Execution failed: {error[:100]}"
    
    def _identify_uncertainty_source(self, thought: str, confidence: float) -> str:
        """Identify why confidence is low."""
        uncertainty_indicators = [
            ("might", "Speculative language detected"),
            ("possibly", "Uncertain conclusion"),
            ("perhaps", "Hypothetical reasoning"),
            ("unsure", "Explicit uncertainty expressed"),
            ("assume", "Unverified assumption made"),
        ]
        
        thought_lower = thought.lower()
        for indicator, reason in uncertainty_indicators:
            if indicator in thought_lower:
                return reason
        
        return "Low confidence without explicit uncertainty markers - may need more information"
    
    def _generate_fix(
        self,
        error_type: ErrorType,
        root_cause: str,
        action: Optional[str]
    ) -> str:
        """Generate a specific fix for the identified issue."""
        fixes = {
            ErrorType.TOOL_EXECUTION: (
                "Validate inputs before tool execution. Add error handling. "
                "Consider alternative tools or manual calculation."
            ),
            ErrorType.LOGICAL_INCONSISTENCY: (
                "Review logical chain for contradictions. Verify each step independently. "
                "Cross-check with known facts."
            ),
            ErrorType.LOW_CONFIDENCE: (
                "Gather more information before concluding. Use wiki_search to verify facts. "
                "Break problem into smaller verifiable steps."
            ),
            ErrorType.CONTEXT_MISMATCH: (
                "Reload relevant context from Wiki. Check conversation history for inconsistencies. "
                "Request clarification from user if needed."
            ),
            ErrorType.FORMAT_VIOLATION: (
                "Ensure strict JSON formatting. Validate against expected schema. "
                "Use proper escaping for special characters."
            ),
            ErrorType.UNKNOWN: (
                "Analyze error message carefully. Try simpler approach first. "
                "Document unexpected behavior for future improvement."
            )
        }
        
        return fixes.get(error_type, "Unknown error type - general debugging required")
    
    def _generate_alternatives(
        self,
        error_type: ErrorType,
        thought: str,
        action: Optional[str]
    ) -> list[str]:
        """Generate alternative approaches to solve the problem."""
        alternatives = []
        
        if error_type == ErrorType.TOOL_EXECUTION:
            alternatives = [
                "Try a different tool that achieves the same goal",
                "Break the operation into smaller steps",
                "Manually compute/verify the result if possible"
            ]
        elif error_type == ErrorType.LOGICAL_INCONSISTENCY:
            alternatives = [
                "Start from first principles and rebuild the argument",
                "Search Wiki for authoritative information on the topic",
                "Ask user to clarify conflicting requirements"
            ]
        elif error_type == ErrorType.LOW_CONFIDENCE:
            alternatives = [
                "Perform additional research via wiki_search",
                "State uncertainty explicitly and provide best estimate",
                "Request more specific information from user"
            ]
        else:
            alternatives = [
                "Retry with modified parameters",
                "Use a different problem-solving strategy",
                "Acknowledge limitation and suggest human review"
            ]
        
        return alternatives
    
    def _calculate_confidence_adjustment(
        self,
        error_type: ErrorType,
        original_confidence: float,
        error: Optional[str]
    ) -> float:
        """Calculate how much to adjust confidence after reflection."""
        # Base adjustments by error type
        adjustments = {
            ErrorType.TOOL_EXECUTION: -0.15,
            ErrorType.LOGICAL_INCONSISTENCY: -0.20,
            ErrorType.LOW_CONFIDENCE: -0.10,
            ErrorType.CONTEXT_MISMATCH: -0.15,
            ErrorType.FORMAT_VIOLATION: -0.05,
            ErrorType.UNKNOWN: -0.10
        }
        
        base_adjustment = adjustments.get(error_type, -0.10)
        
        # Additional penalty if error occurred after previous reflection
        if len(self._reflection_history) > 0:
            base_adjustment -= 0.05
        
        return base_adjustment
    
    def _should_retry(
        self,
        error_type: ErrorType,
        confidence: float,
        num_alternatives: int
    ) -> bool:
        """Determine if retrying is likely to succeed."""
        # Don't retry unknown errors
        if error_type == ErrorType.UNKNOWN:
            return False
        
        # Don't retry if no alternatives available
        if num_alternatives == 0:
            return False
        
        # Don't retry if already very low confidence
        if confidence < 0.3:
            return False
        
        # Do retry for correctable errors
        correctable_types = {
            ErrorType.TOOL_EXECUTION,
            ErrorType.FORMAT_VIOLATION,
            ErrorType.CONTEXT_MISMATCH
        }
        
        return error_type in correctable_types
    
    def get_reflection_summary(self) -> dict[str, Any]:
        """Get summary statistics about reflection history."""
        if not self._reflection_history:
            return {"total_reflections": 0}
        
        error_counts = {}
        for result in self._reflection_history:
            error_name = result.error_type.name
            error_counts[error_name] = error_counts.get(error_name, 0) + 1
        
        return {
            "total_reflections": len(self._reflection_history),
            "error_distribution": error_counts,
            "retry_decisions": sum(
                1 for r in self._reflection_history if r.should_retry
            )
        }
    
    def clear_history(self) -> None:
        """Clear the reflection history."""
        self._reflection_history.clear()
        logger.debug("Reflection history cleared")
