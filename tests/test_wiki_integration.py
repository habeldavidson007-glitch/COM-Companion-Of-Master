"""
COM v3 Integration Tests
=========================
Tests for wiki integration, tool harness, and background service.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWikiIntegration(unittest.TestCase):
    """Test wiki integration in COM core."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test data directories
        self.test_data_dir = Path("./test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        (self.test_data_dir / "raw").mkdir(exist_ok=True)
        (self.test_data_dir / "wiki").mkdir(exist_ok=True)
        (self.test_data_dir / "com_output").mkdir(exist_ok=True)
        
        # Create a sample raw file
        sample_raw = self.test_data_dir / "raw" / "test_article.md"
        sample_raw.write_text("""# Test Article

This is a test article about Python programming.

## Key Points

- Python is a versatile language
- Used for web development, data science, and AI
- Has extensive library ecosystem
""")
    
    def tearDown(self):
        """Clean up test data."""
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    def test_wiki_compiler_import(self):
        """Test that wiki compiler can be imported."""
        try:
            from tools.data_ops.wiki_compiler import WikiCompiler, WikiRetriever
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import wiki compiler: {e}")
    
    def test_wiki_indexer_import(self):
        """Test that wiki indexer can be imported."""
        try:
            from tools.data_ops.wiki_indexer import WikiIndexer
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import wiki indexer: {e}")
    
    def test_tool_harness_wiki_tools(self):
        """Test that tool harness has wiki tools registered."""
        try:
            from tools.tool_harness_wiki import get_available_wiki_tools
            tools = get_available_wiki_tools()
            
            expected_tools = [
                'wiki_compile', 'wiki_compile_all', 'wiki_search',
                'wiki_get_related', 'wiki_create_concept', 
                'wiki_health_check', 'wiki_stats'
            ]
            
            for tool in expected_tools:
                self.assertIn(tool, tools, f"Tool {tool} not registered")
        except ImportError as e:
            self.fail(f"Failed to import tool harness: {e}")
    
    def test_com_core_wiki_integration(self):
        """Test that COM core has wiki integration."""
        try:
            from core.com_core import COMCore, WIKI_AVAILABLE
            
            # Create COM core instance
            com = COMCore()
            
            # Check wiki retriever attribute exists
            self.assertTrue(hasattr(com, 'wiki_retriever'))
            
            # Check knowledge indicators are set
            self.assertTrue(hasattr(com, '_knowledge_indicators'))
            self.assertGreater(len(com._knowledge_indicators), 0)
            
            # Check wiki retrieval method exists
            self.assertTrue(hasattr(com, '_try_wiki_retrieval'))
            
        except Exception as e:
            self.fail(f"COM core wiki integration failed: {e}")
    
    def test_background_service_import(self):
        """Test that background service can be imported."""
        try:
            from background_service import BackgroundWikiService, WikiMaintenanceDaemon
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import background service: {e}")
    
    def test_viewer_import(self):
        """Test that viewer can be imported."""
        try:
            from viewer import WikiViewer
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import viewer: {e}")


class TestWikiCompiler(unittest.TestCase):
    """Test wiki compiler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path("./test_compiler_data")
        self.test_data_dir.mkdir(exist_ok=True)
        (self.test_data_dir / "raw").mkdir(exist_ok=True)
        (self.test_data_dir / "wiki").mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test data."""
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    def test_compile_file(self):
        """Test compiling a single file."""
        from tools.data_ops.wiki_compiler import WikiCompiler
        
        # Create test file
        test_file = self.test_data_dir / "raw" / "test.md"
        test_file.write_text("# Test\n\nContent here.")
        
        compiler = WikiCompiler(data_dir=str(self.test_data_dir))
        result = compiler.compile_file(str(test_file))
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Test')
        self.assertTrue(Path(result['wiki']).exists())
    
    def test_wiki_search(self):
        """Test wiki search functionality."""
        from tools.data_ops.wiki_compiler import WikiCompiler, WikiRetriever
        
        # Create and compile test file
        test_file = self.test_data_dir / "raw" / "python_test.md"
        test_file.write_text("""# Python Programming

Python is a programming language used for AI and web development.
""")
        
        compiler = WikiCompiler(data_dir=str(self.test_data_dir))
        compiler.compile_file(str(test_file))
        
        # Search
        retriever = WikiRetriever(data_dir=str(self.test_data_dir))
        results = retriever.search("python AI", top_k=5)
        
        # Should find the document
        self.assertGreater(len(results), 0)


class TestSystemPrompt(unittest.TestCase):
    """Test system prompt v3."""
    
    def test_system_prompt_content(self):
        """Test that system prompt contains key phrases."""
        from system_prompt_v3 import SYSTEM_PROMPT_V3, SYSTEM_PROMPT_V3_SHORT
        
        # Check for key concepts
        self.assertIn("EDITOR", SYSTEM_PROMPT_V3)
        self.assertIn("Writer", SYSTEM_PROMPT_V3)
        self.assertIn("wiki", SYSTEM_PROMPT_V3.lower())
        self.assertIn("[ACTION:", SYSTEM_PROMPT_V3)
        
        # Short version should also have key info
        self.assertIn("EDITOR", SYSTEM_PROMPT_V3_SHORT)
        self.assertIn("wiki", SYSTEM_PROMPT_V3_SHORT.lower())


if __name__ == '__main__':
    print("Running COM v3 Integration Tests...")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2)
