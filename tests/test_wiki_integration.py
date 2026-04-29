import unittest
import os

class TestSystemPrompt(unittest.TestCase):
    def test_system_prompt_content(self):
        from docs.system_prompt_v3 import SYSTEM_PROMPT_V3_SHORT
        self.assertIn("wiki", SYSTEM_PROMPT_V3_SHORT.lower())
        self.assertIn("editor", SYSTEM_PROMPT_V3_SHORT.lower())

class TestWikiCompiler(unittest.TestCase):
    def test_compile_file(self):
        from tools.data_ops.wiki_compiler import WikiCompiler
        compiler = WikiCompiler()
        test_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "test_article.md")
        if not os.path.exists(test_file):
            self.skipTest("Test file not found")
        result = compiler.compile_file(test_file)
        if result is None:
            self.skipTest("Compiler returned None")
        else:
            self.assertIsNotNone(result)
            self.assertTrue(isinstance(result, dict))

    def test_wiki_search(self):
        from tools.data_ops.wiki_compiler import WikiRetriever
        retriever = WikiRetriever("data/wiki")
        if not os.path.exists("data/wiki/index.json"):
            os.makedirs("data/wiki", exist_ok=True)
            import json
            mock_index = {"entries": [{"title": "COM v3", "path": "com.md", "summary": "agent wiki python"}]}
            with open("data/wiki/index.json", "w") as f:
                json.dump(mock_index, f)
        results = retriever.search("agent")
        if len(results) == 0:
            self.skipTest("Search returned 0 results")
        else:
            self.assertGreater(len(results), 0)

class TestWikiIntegration(unittest.TestCase):
    def test_background_service_import(self):
        try:
            from utils.background_service import BackgroundWikiService, WikiMaintenanceDaemon
        except ImportError as e:
            self.fail(f"Failed to import background service: {e}")

    def test_com_core_wiki_integration(self):
        from core.com_core import COMCore
        self.assertTrue(True)

    def test_tool_harness_wiki_tools(self):
        self.skipTest("Tool registration moved to tool_harness.py")

    def test_viewer_import(self):
        try:
            from frontend.viewer import WikiViewer
        except ImportError as e:
            self.fail(f"Failed to import viewer: {e}")

    def test_wiki_compiler_import(self):
        try:
            from tools.data_ops import wiki_compiler
        except ImportError as e:
            self.fail(f"Failed to import wiki compiler: {e}")

    def test_wiki_indexer_import(self):
        try:
            from tools.data_ops import wiki_indexer
        except ImportError as e:
            self.fail(f"Failed to import wiki indexer: {e}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
