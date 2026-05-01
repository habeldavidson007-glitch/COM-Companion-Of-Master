"""
Test module for signal_schema.py

Tests:
1. Schema instantiation with valid data
2. Schema validation rejects invalid data
3. Property accessors work correctly
4. Schema registry lookup functions
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.signal_schema import (
    SignalSchema,
    ValidateNodePath,
    ExplainError,
    RefactorSafe,
    SCHEMA_REGISTRY,
    get_schema_for_action,
    validate_schema_instance,
)


class TestValidateNodePath:
    """Tests for ValidateNodePath schema."""
    
    def test_create_valid_schema(self):
        """Test creating a valid ValidateNodePath instance."""
        schema = ValidateNodePath(
            params={
                "node_path": "root/Player/Sprite",
                "expected_type": "Sprite2D",
                "is_valid": True,
                "reason": "Valid path structure"
            },
            constraints=["Do not create nodes"]
        )
        
        assert schema.action == "validate_node_path"
        assert schema.node_path == "root/Player/Sprite"
        assert schema.is_valid is True
    
    def test_property_accessors(self):
        """Test that property accessors return correct values."""
        schema = ValidateNodePath(
            params={
                "node_path": "root/Enemy",
                "is_valid": False,
                "reason": "Node does not exist"
            }
        )
        
        assert schema.node_path == "root/Enemy"
        assert schema.is_valid is False
    
    def test_null_values_allowed(self):
        """Test that null values are allowed for uncertain cases."""
        schema = ValidateNodePath(
            params={
                "node_path": "unknown/path",
                "is_valid": None,  # Uncertain
                "reason": ""
            }
        )
        
        assert schema.is_valid is None


class TestExplainError:
    """Tests for ExplainError schema."""
    
    def test_create_valid_schema(self):
        """Test creating a valid ExplainError instance."""
        schema = ExplainError(
            params={
                "error_log": "Attempt to call function on null instance",
                "explanation": "Node reference is null",
                "suggested_fix": "Check node path and loading order",
                "confidence": 0.85,
                "wiki_references": ["@GDScript.get_node"]
            },
            context="Scene loading"
        )
        
        assert schema.action == "explain_error"
        assert schema.explanation == "Node reference is null"
        assert schema.suggested_fix == "Check node path and loading order"
        assert schema.params["confidence"] == 0.85
    
    def test_property_accessors(self):
        """Test that property accessors work correctly."""
        schema = ExplainError(
            params={
                "error_log": "Some error",
                "explanation": "Explanation text",
                "suggested_fix": "Fix steps"
            }
        )
        
        assert schema.error_log == "Some error"
        assert schema.explanation == "Explanation text"
        assert schema.suggested_fix == "Fix steps"


class TestRefactorSafe:
    """Tests for RefactorSafe schema."""
    
    def test_create_valid_schema(self):
        """Test creating a valid RefactorSafe instance."""
        schema = RefactorSafe(
            params={
                "target_file": "player.gd",
                "proposed_change": "Extract movement logic",
                "affected_nodes": ["Player"],
                "rollback_plan": "Restore original code",
                "risk_level": "low"
            },
            constraints=["Preserve public API"]
        )
        
        assert schema.action == "refactor_safe"
        assert schema.target_file == "player.gd"
        assert schema.risk_level == "low"
        assert len(schema.affected_nodes) == 1
    
    def test_risk_levels(self):
        """Test different risk levels."""
        for level in ["low", "medium", "high"]:
            schema = RefactorSafe(
                params={"risk_level": level}
            )
            assert schema.risk_level == level


class TestSchemaRegistry:
    """Tests for schema registry functions."""
    
    def test_registry_contains_all_schemas(self):
        """Test that registry contains all expected schemas."""
        expected_actions = ["validate_node_path", "explain_error", "refactor_safe"]
        
        for action in expected_actions:
            assert action in SCHEMA_REGISTRY
    
    def test_get_schema_for_action(self):
        """Test getting schema class by action name."""
        assert get_schema_for_action("validate_node_path") == ValidateNodePath
        assert get_schema_for_action("explain_error") == ExplainError
        assert get_schema_for_action("refactor_safe") == RefactorSafe
        assert get_schema_for_action("unknown_action") is None
    
    def test_validate_schema_instance(self):
        """Test schema instance validation."""
        valid_schema = ValidateNodePath(params={"node_path": "test"})
        assert validate_schema_instance(valid_schema) is True
        
        # Invalid: not a SignalSchema
        assert validate_schema_instance({"not": "a schema"}) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
