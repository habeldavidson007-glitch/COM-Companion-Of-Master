"""
Signal Schema Module - Frozen JSON Schema v1.0 for LLM output enforcement.

CRITICAL: This module defines the contract between the LLM and the system.
All LLM outputs MUST conform to these schemas. The instructor library
enforces schema validation with auto-retry (up to 3 times) before failing safely.

Architecture Principle: Zero Hallucination
- Structural facts (node paths, file names) come from parsing (watchfiles, regex)
- LLM only interprets and explains, never invents structural information

Schemas Defined:
1. ValidateNodePath - Verify a Godot node path exists
2. ExplainError - Analyze and explain an error log
3. RefactorSafe - Safe refactoring plan with constraints
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class SignalSchema(BaseModel):
    """
    Base schema for all signal types.
    
    Every signal must have:
    - action: The type of operation being performed
    - params: Parameters specific to the action
    - context: Relevant context information
    - constraints: Limitations or safety requirements
    
    This base class ensures consistent structure across all signal types.
    """
    action: str = Field(..., description="The action type (e.g., 'validate', 'explain', 'refactor')")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    context: Optional[str] = Field(None, description="Relevant context for the action")
    constraints: List[str] = Field(default_factory=list, description="Safety constraints or limitations")
    
    class Config:
        extra = "forbid"  # Reject unexpected fields
        frozen = False  # Allow modification during validation retry


class ValidateNodePath(SignalSchema):
    """
    Schema for validating a Godot node path.
    
    Used when user asks to verify if a node path exists or is correct.
    The LLM should NOT guess paths - it should return null if uncertain.
    
    Fields:
        node_path: The path to validate (e.g., "root/Player/Sprite")
        expected_type: Expected node type if known (e.g., "Sprite2D")
        is_valid: Whether the path is valid (null if uncertain)
        reason: Explanation of validity status
        
    Example:
        {
            "action": "validate_node_path",
            "params": {
                "node_path": "root/Player/Sprite",
                "expected_type": "Sprite2D",
                "is_valid": true,
                "reason": "Path follows Godot naming conventions"
            },
            "constraints": ["Do not create nodes, only validate"]
        }
    """
    action: Literal["validate_node_path"] = "validate_node_path"
    params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "node_path": "",
            "expected_type": None,
            "is_valid": None,
            "reason": ""
        }
    )
    
    @property
    def node_path(self) -> str:
        return self.params.get("node_path", "")
    
    @property
    def is_valid(self) -> Optional[bool]:
        return self.params.get("is_valid")


class ExplainError(SignalSchema):
    """
    Schema for explaining Godot error logs.
    
    Used when user needs help understanding an error message.
    The LLM should provide clear explanation and suggested fix.
    
    Critical: Wiki snippets are injected BEFORE LLM call to prevent hallucination.
    
    Fields:
        error_log: The original error message
        explanation: Clear explanation of what went wrong
        suggested_fix: Concrete steps to resolve the issue
        confidence: How confident the LLM is (0.0 to 1.0)
        wiki_references: Relevant wiki snippets used (injected by retriever)
        
    Example:
        {
            "action": "explain_error",
            "params": {
                "error_log": "Attempt to call function 'get_node' on a null instance",
                "explanation": "The node you're trying to access doesn't exist at runtime",
                "suggested_fix": "Check if the node path is correct and the node is loaded",
                "confidence": 0.9,
                "wiki_references": ["@GDScript.get_node", "SceneTree"]
            },
            "context": "User is loading scene asynchronously"
        }
    """
    action: Literal["explain_error"] = "explain_error"
    params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "error_log": "",
            "explanation": "",
            "suggested_fix": "",
            "confidence": 0.0,
            "wiki_references": []
        }
    )
    
    @property
    def error_log(self) -> str:
        return self.params.get("error_log", "")
    
    @property
    def explanation(self) -> str:
        return self.params.get("explanation", "")
    
    @property
    def suggested_fix(self) -> str:
        return self.params.get("suggested_fix", "")


class RefactorSafe(SignalSchema):
    """
    Schema for safe refactoring operations.
    
    Used when user wants to modify code structure.
    CRITICAL: This schema enforces safety constraints to prevent breaking changes.
    
    Fields:
        target_file: File to refactor
        current_code: Current code snippet
        proposed_change: Description of the change
        affected_nodes: List of nodes that might be affected
        rollback_plan: Steps to undo the change if needed
        risk_level: low/medium/high assessment
        
    Example:
        {
            "action": "refactor_safe",
            "params": {
                "target_file": "player.gd",
                "current_code": "func _ready(): ...",
                "proposed_change": "Extract movement logic to separate function",
                "affected_nodes": ["Player", "Player/CollisionShape2D"],
                "rollback_plan": "Restore original _ready() implementation",
                "risk_level": "low"
            },
            "constraints": [
                "Do not modify signal connections",
                "Preserve public API",
                "Test in isolated scene first"
            ]
        }
    """
    action: Literal["refactor_safe"] = "refactor_safe"
    params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "target_file": "",
            "current_code": "",
            "proposed_change": "",
            "affected_nodes": [],
            "rollback_plan": "",
            "risk_level": "low"
        }
    )
    
    @property
    def target_file(self) -> str:
        return self.params.get("target_file", "")
    
    @property
    def risk_level(self) -> str:
        return self.params.get("risk_level", "low")
    
    @property
    def affected_nodes(self) -> List[str]:
        return self.params.get("affected_nodes", [])


# Schema registry for intent_router lookup
SCHEMA_REGISTRY: Dict[str, type] = {
    "validate_node_path": ValidateNodePath,
    "explain_error": ExplainError,
    "refactor_safe": RefactorSafe,
}


class SchemaRegistry:
    """Wrapper class for schema registry operations."""
    
    _registry = SCHEMA_REGISTRY.copy()
    
    @classmethod
    def get(cls, action: str) -> Optional[type]:
        """Get schema class by action name."""
        return cls._registry.get(action)
    
    @classmethod
    def register(cls, action: str, schema_class: type) -> None:
        """Register a new schema class."""
        cls._registry[action] = schema_class
    
    @classmethod
    def list_actions(cls) -> List[str]:
        """List all registered actions."""
        return list(cls._registry.keys())


def get_schema_for_action(action: str) -> Optional[type]:
    """
    Get the schema class for a given action type.
    
    Args:
        action: Action name (e.g., "validate_node_path")
    
    Returns:
        Schema class or None if action not recognized.
    """
    return SCHEMA_REGISTRY.get(action)


def validate_schema_instance(instance: SignalSchema) -> bool:
    """
    Validate that a schema instance meets all requirements.
    
    Args:
        instance: Schema instance to validate.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(instance, SignalSchema):
        return False
    
    # Check required fields
    if not instance.action:
        return False
    
    # Additional validation can be added here
    return True


if __name__ == "__main__":
    # Test schema creation
    print("=" * 50)
    print("Signal Schema Test")
    print("=" * 50)
    
    # Test ValidateNodePath
    validate = ValidateNodePath(
        params={
            "node_path": "root/Player/Sprite",
            "expected_type": "Sprite2D",
            "is_valid": True,
            "reason": "Valid path structure"
        },
        constraints=["Do not create nodes"]
    )
    print(f"ValidateNodePath: {validate}")
    print(f"Node Path: {validate.node_path}")
    print(f"Is Valid: {validate.is_valid}")
    
    # Test ExplainError
    explain = ExplainError(
        params={
            "error_log": "Attempt to call function on null instance",
            "explanation": "Node reference is null",
            "suggested_fix": "Check node path and loading order",
            "confidence": 0.85,
            "wiki_references": ["@GDScript.get_node"]
        },
        context="Scene loading"
    )
    print(f"\nExplainError: {explain}")
    print(f"Explanation: {explain.explanation}")
    
    # Test RefactorSafe
    refactor = RefactorSafe(
        params={
            "target_file": "player.gd",
            "proposed_change": "Extract movement logic",
            "affected_nodes": ["Player"],
            "rollback_plan": "Restore original code",
            "risk_level": "low"
        },
        constraints=["Preserve public API"]
    )
    print(f"\nRefactorSafe: {refactor}")
    print(f"Risk Level: {refactor.risk_level}")
    
    # Test schema registry
    print(f"\nSchema Registry: {list(SCHEMA_REGISTRY.keys())}")
    
    print("=" * 50)
