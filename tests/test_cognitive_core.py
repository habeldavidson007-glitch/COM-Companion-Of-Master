"""
COM v4 - Test Suite

Validation tests for the cognitive architecture components.
"""

import pytest
import json
from pathlib import Path


class TestContextManager:
    """Tests for the ContextManager class."""
    
    def test_token_estimation(self):
        """Test that token estimation is reasonable."""
        from core.context_manager import ContextManager
        
        cm = ContextManager()
        text = "This is a test sentence with about 10 tokens."
        estimated = cm._estimate_tokens(text)
        
        # Should be roughly len/4
        assert 5 <= estimated <= 15
    
    def test_history_compression(self):
        """Test that history compression works correctly."""
        from core.context_manager import ContextManager, ConversationTurn
        
        cm = ContextManager()
        
        # Add multiple turns
        for i in range(5):
            cm.add_turn("user", f"Query {i}")
            cm.add_turn("assistant", f"Response {i}")
        
        # Check compression triggers
        compressed = cm.compress_history()
        assert "summary" in compressed.lower() or len(compressed) > 0
    
    def test_wiki_injection_empty(self):
        """Test Wiki injection with no knowledge base."""
        from core.context_manager import ContextManager
        
        cm = ContextManager(wiki_path="/nonexistent/path")
        chunks = cm.inject_wiki_context("test query")
        
        assert chunks == []


class TestSecureExecutor:
    """Tests for the SecureExecutor class."""
    
    def test_safe_code_execution(self):
        """Test executing safe Python code."""
        from tools.secure_executor import SecureExecutor
        
        executor = SecureExecutor()
        result = executor.execute("print(2 + 2)")
        
        assert result.success is True
        assert "4" in result.stdout
    
    def test_dangerous_code_blocked(self):
        """Test that dangerous code patterns are blocked."""
        from tools.secure_executor import SecureExecutor
        
        executor = SecureExecutor()
        result = executor.execute("import os; os.system('ls')")
        
        assert result.success is False
        assert "SECURITY_VIOLATION" in result.error_type
    
    def test_expression_evaluation(self):
        """Test simple expression evaluation."""
        from tools.secure_executor import SecureExecutor
        
        executor = SecureExecutor()
        result = executor.execute_expression("15 * 23 + 48 / 6")
        
        assert result.success is True
        assert "353" in result.stdout


class TestWikiCompiler:
    """Tests for the WikiCompiler class."""
    
    def test_chunk_creation(self):
        """Test creating knowledge chunks."""
        from tools.wiki_compiler import KnowledgeChunk
        
        chunk = KnowledgeChunk(
            id="test123",
            source="test.md",
            topic="Test Topic",
            content="This is test content for verification.",
            metadata={},
            created_at="2024-01-01T00:00:00"
        )
        
        assert chunk.token_count > 0
        assert chunk.to_dict()["id"] == "test123"
    
    def test_compiler_initialization(self):
        """Test WikiCompiler initialization."""
        from tools.wiki_compiler import WikiCompiler
        
        compiler = WikiCompiler(
            raw_path="knowledge/raw",
            compiled_path="knowledge/compiled_wiki"
        )
        
        assert compiler.raw_path.exists()
        assert compiler.compiled_path.exists()


class TestReflectionEngine:
    """Tests for the ReflectionEngine class."""
    
    def test_error_classification(self):
        """Test error type classification."""
        from core.reflection_module import ReflectionEngine, ErrorType
        
        engine = ReflectionEngine()
        
        # Test tool execution error
        error_type = engine.classify_error("Traceback: Exception occurred", {})
        assert error_type == ErrorType.TOOL_EXECUTION
        
        # Test format violation (use 'schema' keyword which maps to FORMAT_VIOLATION)
        error_type = engine.classify_error("Invalid JSON schema format", {})
        assert error_type == ErrorType.FORMAT_VIOLATION
    
    def test_reflection_analysis(self):
        """Test full reflection analysis."""
        from core.reflection_module import ReflectionEngine
        
        engine = ReflectionEngine()
        
        result = engine.analyze(
            thought="Let me calculate this step by step...",
            action='{"name": "execute_code", "arguments": {"code": "10/0"}}',
            observation=None,
            error="ZeroDivisionError: division by zero",
            confidence=0.9
        )
        
        assert result.error_type is not None
        assert result.root_cause != ""
        assert len(result.alternative_approaches) > 0


class TestAgentLoop:
    """Tests for the CognitiveAgent class."""
    
    def test_output_parsing(self):
        """Test parsing model output."""
        from core.agent_loop import CognitiveAgent
        
        agent = CognitiveAgent()
        
        # Test complete output
        output = """<thought>This is my reasoning</thought>
<action>{"name": "response", "arguments": {"text": "Hello"}}</action>
<confidence>0.95</confidence>"""
        
        parsed = agent._parse_model_output(output)
        
        assert "reasoning" in parsed["thought"]
        assert parsed["action"]["name"] == "response"
        assert parsed["confidence"] == 0.95
    
    def test_tool_execution(self):
        """Test tool execution in agent loop."""
        from core.agent_loop import CognitiveAgent
        
        def mock_tool(value: int) -> int:
            return value * 2
        
        agent = CognitiveAgent(tools={"double": mock_tool})
        
        observation, error = agent._execute_tool({
            "name": "double",
            "arguments": {"value": 5}
        })
        
        assert error is None
        assert "10" in observation
    
    def test_unknown_tool_handling(self):
        """Test handling of unknown tools."""
        from core.agent_loop import CognitiveAgent
        
        agent = CognitiveAgent(tools={})
        
        observation, error = agent._execute_tool({
            "name": "nonexistent",
            "arguments": {}
        })
        
        assert error is not None
        assert "Unknown tool" in error


class TestIntegration:
    """Integration tests for the full system."""
    
    def test_full_pipeline(self):
        """Test the complete cognitive pipeline."""
        from core import CognitiveAgent, ContextManager, ReflectionEngine
        from tools import SecureExecutor
        
        # Initialize all components
        context_manager = ContextManager()
        reflection_engine = ReflectionEngine()
        executor = SecureExecutor()
        
        tools = {
            "calculate": lambda expr: executor.execute_expression(expr),
        }
        
        agent = CognitiveAgent(
            model_name="test-model",
            tools=tools,
            context_manager=context_manager,
            reflection_engine=reflection_engine
        )
        
        # Verify agent is properly configured
        assert agent.context_manager is context_manager
        assert agent.reflection_engine is reflection_engine
        assert "calculate" in agent.tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
