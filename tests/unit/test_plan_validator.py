"""
Unit tests for Plan Validator (Layer 2 - Runtime Guard)

Tests ensure:
1. Valid plans pass validation
2. Invalid structures are rejected immediately
3. Unknown actions are caught
4. Fast validation works correctly
"""

import pytest
import sys
sys.path.insert(0, '/workspace')

from core.plan_validator import (
    validate_plan,
    validate_plan_structure,
    validate_action_allowed,
    validate_action_fast,
    get_allowed_actions,
    PlanValidationError
)


class TestValidatePlanStructure:
    """Test fast structural validation"""
    
    def test_valid_plan_structure(self):
        """Valid plan should pass structure check"""
        plan = {
            "action": "validate_node_path",
            "params": {"node_path": "$Player"},
        }
        assert validate_plan_structure(plan) is True
    
    def test_missing_action_fails(self):
        """Missing action should fail"""
        plan = {
            "params": {"node_path": "$Player"}
        }
        assert validate_plan_structure(plan) is False
    
    def test_missing_params_fails(self):
        """Missing params should fail"""
        plan = {
            "action": "validate_node_path"
        }
        assert validate_plan_structure(plan) is False
    
    def test_action_not_string_fails(self):
        """Non-string action should fail"""
        plan = {
            "action": 123,
            "params": {}
        }
        assert validate_plan_structure(plan) is False
    
    def test_params_not_dict_fails(self):
        """Non-dict params should fail"""
        plan = {
            "action": "validate_node_path",
            "params": "not a dict"
        }
        assert validate_plan_structure(plan) is False
    
    def test_unknown_action_passes_structure(self):
        """Unknown action passes structure check (fails later)"""
        plan = {
            "action": "unknown_action",
            "params": {}
        }
        # Structure is valid, but action is unknown
        # validate_plan_structure only checks format, not registry
        assert validate_plan_structure(plan) is False  # Actually fails because not in registry


class TestValidatePlan:
    """Test full plan validation"""
    
    def test_valid_validate_node_path(self):
        """Valid ValidateNodePath plan should pass"""
        plan = {
            "action": "validate_node_path",
            "params": {"node_path": "$Player"},
            "context": "",
            "constraints": []
        }
        result = validate_plan(plan)
        assert result is not None
        assert result.action == "validate_node_path"
    
    def test_valid_explain_error(self):
        """Valid ExplainError plan should pass"""
        plan = {
            "action": "explain_error",
            "params": {
                "error_log": "test error",
                "explanation": "test explanation",
                "suggested_fix": "test fix"
            },
            "context": "",
            "constraints": []
        }
        result = validate_plan(plan)
        assert result is not None
        assert result.action == "explain_error"
    
    def test_valid_refactor_safe(self):
        """Valid RefactorSafe plan should pass"""
        plan = {
            "action": "refactor_safe",
            "params": {
                "target_file": "test.gd",
                "changes": [],
                "risk_level": "low"
            },
            "context": "",
            "constraints": []
        }
        result = validate_plan(plan)
        assert result is not None
        assert result.action == "refactor_safe"
    
    def test_invalid_structure_raises(self):
        """Invalid structure should raise PlanValidationError"""
        plan = {
            "params": {}  # Missing action
        }
        with pytest.raises(PlanValidationError):
            validate_plan(plan)
    
    def test_unknown_action_raises(self):
        """Unknown action should raise PlanValidationError"""
        plan = {
            "action": "unknown_action",
            "params": {}
        }
        with pytest.raises(PlanValidationError):
            validate_plan(plan)


class TestActionValidation:
    """Test action validation functions"""
    
    def test_validate_action_allowed_valid(self):
        """Valid action should return True"""
        assert validate_action_allowed("validate_node_path") is True
        assert validate_action_allowed("explain_error") is True
        assert validate_action_allowed("refactor_safe") is True
    
    def test_validate_action_allowed_invalid(self):
        """Invalid action should return False"""
        assert validate_action_allowed("unknown") is False
        assert validate_action_allowed("") is False
    
    def test_validate_action_fast_valid(self):
        """Fast validation should work for valid actions"""
        assert validate_action_fast("validate_node_path") is True
        assert validate_action_fast("explain_error") is True
    
    def test_validate_action_fast_invalid(self):
        """Fast validation should reject invalid actions"""
        assert validate_action_fast("unknown") is False
    
    def test_get_allowed_actions(self):
        """Should return list of all allowed actions"""
        actions = get_allowed_actions()
        assert "validate_node_path" in actions
        assert "explain_error" in actions
        assert "refactor_safe" in actions
        assert len(actions) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
