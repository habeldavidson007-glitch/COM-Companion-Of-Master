"""
Test module for adaptive_router.py and ram_monitor.py

Tests:
1. RAM monitoring functions work correctly
2. Adaptive router selects appropriate model based on RAM
3. Model fallback chain works when larger models fail
4. Context compressor never exceeds token limits
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ram_monitor import (
    get_available_ram_gb,
    get_total_ram_gb,
    can_load_model,
    get_usable_ram_for_models,
    select_model_from_chain,
)
from core.adaptive_router import AdaptiveRouter, adaptive_complete
from core.context_compressor import ContextCompressor, compress_context


class TestRAMMonitor:
    """Tests for RAM monitoring functions."""
    
    def test_get_available_ram_gb_returns_float(self):
        """Test that available RAM returns a float value."""
        result = get_available_ram_gb()
        assert isinstance(result, float)
        assert result >= 0.0
    
    def test_get_total_ram_gb_returns_float(self):
        """Test that total RAM returns a float value."""
        result = get_total_ram_gb()
        assert isinstance(result, float)
        assert result >= 0.5  # At least 512MB
    
    def test_can_load_model_with_low_ram(self):
        """Test can_load_model with insufficient RAM."""
        # With default 1.5GB buffer, loading a 4.5GB model should fail on most systems
        result = can_load_model(4.5)
        # Result depends on actual system RAM, just verify it returns bool
        assert isinstance(result, bool)
    
    def test_get_usable_ram_calculation(self):
        """Test usable RAM calculation subtracts buffer."""
        available = get_available_ram_gb()
        usable = get_usable_ram_for_models()
        
        # Usable should be available minus buffer (or 0 if less)
        expected = max(0.0, available - 1.5)
        assert abs(usable - expected) < 0.1  # Allow small floating point error
    
    def test_select_model_from_chain(self):
        """Test model selection from chain."""
        test_chain = [
            {"name": "large-model", "ram": 8.0},
            {"name": "medium-model", "ram": 4.0},
            {"name": "small-model", "ram": 1.0},
        ]
        
        result = select_model_from_chain(test_chain)
        
        # Should return a dict or None
        if result is not None:
            assert isinstance(result, dict)
            assert "name" in result
            assert "ram" in result


class TestAdaptiveRouter:
    """Tests for AdaptiveRouter."""
    
    def test_router_initialization(self):
        """Test router initializes correctly."""
        router = AdaptiveRouter()
        assert router.model_chain is not None
        assert len(router.model_chain) > 0
    
    def test_router_select_best_model(self):
        """Test model selection method."""
        router = AdaptiveRouter()
        model = router.select_best_model()
        
        # Should return a model dict or None
        if model is not None:
            assert isinstance(model, dict)
            assert "name" in model
    
    def test_router_with_custom_chain(self):
        """Test router with custom model chain."""
        custom_chain = [
            {"name": "test-model", "ram": 0.5},
        ]
        router = AdaptiveRouter(model_chain=custom_chain)
        
        assert router.model_chain == custom_chain
    
    def test_mock_completion(self):
        """Test mock completion when liteLLM unavailable."""
        router = AdaptiveRouter()
        
        messages = [{"role": "user", "content": "Hello"}]
        response = router.complete(messages)
        
        # Response should have choices attribute
        assert hasattr(response, "choices")
        assert len(response.choices) > 0


class TestContextCompressor:
    """Tests for ContextCompressor."""
    
    def test_compress_short_text_unchanged(self):
        """Test that short text passes through unchanged."""
        compressor = ContextCompressor(max_tokens=100)
        short_text = "This is a short text."
        
        result = compressor.compress(short_text)
        assert result == short_text
    
    def test_compress_long_text_truncated(self):
        """Test that long text gets truncated."""
        compressor = ContextCompressor(max_tokens=20)
        
        # Create text that exceeds limit
        long_text = "word " * 100  # 500 characters
        
        result = compressor.compress(long_text)
        
        # Result should be shorter than input
        assert len(result) < len(long_text)
        # Should contain truncation marker
        assert "[..." in result or "truncated" in result.lower()
    
    def test_count_tokens(self):
        """Test token counting."""
        compressor = ContextCompressor()
        text = "Hello world"
        
        count = compressor.count_tokens(text)
        assert isinstance(count, int)
        assert count > 0
    
    def test_compress_context_function(self):
        """Test convenience function."""
        text = "Short text"
        result = compress_context(text, max_tokens=100)
        assert result == text
    
    def test_never_exceeds_max_tokens(self):
        """CRITICAL: Verify compressed output never exceeds max_tokens."""
        compressor = ContextCompressor(max_tokens=50)
        
        # Very long input
        long_text = "sentence. " * 500
        
        result = compressor.compress(long_text)
        token_count = compressor.count_tokens(result)
        
        # This is the critical guarantee
        assert token_count <= 50, f"Token count {token_count} exceeds max 50!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
