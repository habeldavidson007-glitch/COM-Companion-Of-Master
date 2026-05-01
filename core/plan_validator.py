"""
Plan Validator - Runtime Guard (Layer 2)

This module provides lightweight, O(1) validation for LLM-generated plans.
It is NOT a test suite - it's a runtime guard that ensures:
1. Plans conform to expected structure before execution
2. Invalid plans are rejected immediately (fail-fast)
3. Zero overhead for valid plans

Architecture Decision:
- This is NOT TDD, it's a production runtime guard
- Validation must be fast (<1ms)
- No heavy logic, only structural checks
"""

from typing import Dict, Any, Optional, List
from core.signal_schema import (
    ValidateNodePath,
    ExplainError,
    RefactorSafe,
    SCHEMA_REGISTRY,
    SignalSchema
)


class PlanValidationError(Exception):
    """Raised when a plan fails validation."""
    pass


def validate_plan_structure(plan: Dict[str, Any]) -> bool:
    """
    Fast structural validation of a plan dictionary.
    
    Checks:
    1. 'action' field exists and is a string
    2. 'params' field exists and is a dict
    3. Action is in the known registry
    
    Returns:
        bool: True if valid, False otherwise
    
    Time Complexity: O(1)
    """
    # Check action exists
    if "action" not in plan:
        return False
    
    if not isinstance(plan["action"], str):
        return False
    
    # Check params exists
    if "params" not in plan:
        return False
    
    if not isinstance(plan["params"], dict):
        return False
    
    # Check action is known
    if plan["action"] not in SCHEMA_REGISTRY:
        return False
    
    return True


def validate_plan(plan: Dict[str, Any]) -> Optional[SignalSchema]:
    """
    Validate a plan dictionary and return instantiated schema.
    
    This is the main entry point for plan validation before execution.
    
    Args:
        plan: Dictionary containing action, params, context, constraints
        
    Returns:
        SignalSchema instance if valid, None if invalid
        
    Raises:
        PlanValidationError: If plan structure is invalid
        
    Example:
        >>> plan = {
        ...     "action": "validate_node_path",
        ...     "params": {"node_path": "$Player"}
        ... }
        >>> schema = validate_plan(plan)
        >>> if schema:
        ...     execute_plan(schema)
    """
    # Fast structural check first
    if not validate_plan_structure(plan):
        raise PlanValidationError("Plan structure invalid")
    
    # Get schema class from registry
    schema_class = SCHEMA_REGISTRY.get(plan["action"])
    if schema_class is None:
        raise PlanValidationError(f"Unknown action: {plan['action']}")
    
    try:
        # Instantiate schema - this triggers Pydantic validation
        # instructor will have already validated, but we double-check
        instance = schema_class(**plan)
        return instance
    except Exception as e:
        raise PlanValidationError(f"Schema validation failed: {str(e)}")


def validate_action_allowed(action: str) -> bool:
    """
    Check if an action type is allowed.
    
    Time Complexity: O(1)
    """
    return action in SCHEMA_REGISTRY


def get_allowed_actions() -> List[str]:
    """
    Get list of all allowed action types.
    
    Returns:
        List of action strings
    """
    return list(SCHEMA_REGISTRY.keys())


# Pre-computed set for fastest possible lookup
_ALLOWED_ACTIONS_SET = frozenset(get_allowed_actions())


def validate_action_fast(action: str) -> bool:
    """
    Ultra-fast action validation using pre-computed frozenset.
    
    Use this in hot paths where every microsecond counts.
    
    Time Complexity: O(1) average case
    """
    return action in _ALLOWED_ACTIONS_SET


if __name__ == "__main__":
    # Test validation
    print("=" * 50)
    print("Plan Validator Test")
    print("=" * 50)
    
    # Valid plan
    valid_plan = {
        "action": "validate_node_path",
        "params": {"node_path": "$Player"},
        "context": "",
        "constraints": []
    }
    
    result = validate_plan(valid_plan)
    print(f"Valid plan: {result is not None}")
    print(f"Schema type: {type(result).__name__}")
    
    # Invalid plan (missing action)
    invalid_plan = {
        "params": {"node_path": "$Player"}
    }
    
    try:
        validate_plan(invalid_plan)
        print("ERROR: Should have raised exception")
    except PlanValidationError as e:
        print(f"Invalid plan caught: {e}")
    
    # Unknown action
    unknown_plan = {
        "action": "unknown_action",
        "params": {}
    }
    
    try:
        validate_plan(unknown_plan)
        print("ERROR: Should have raised exception")
    except PlanValidationError as e:
        print(f"Unknown action caught: {e}")
    
    # Fast validation
    print(f"\nFast validation: {validate_action_fast('validate_node_path')}")
    print(f"Allowed actions: {get_allowed_actions()}")
    
    print("=" * 50)
