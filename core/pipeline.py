"""
Master Pipeline Orchestrator for COM IDE.
Flow: Input → Parse (Rule) → Wiki (Enrich) → LLM (JSON Plan) → Harness (Execute) → Output
"""
import os
from typing import Any, Optional
from pathlib import Path
import logfire

from .signal_schema import SchemaRegistry, ValidateNodePath, ExplainError, RefactorSafe
from .intent_router import IntentRouter
from .wiki_retriever import WikiRetriever
from .context_compressor import compress_context
from .adaptive_router import AdaptiveRouter
from .cache_manager import cache_manager
from .ram_hardener import ram_hardener, ram_safe

logfire.configure(send_to_logfire=False)

class CompilerPipeline:
    """
    The main pipeline orchestrator implementing the "Compiler-Lite" architecture.
    
    Design decisions:
    - Single-pass execution: No chatbot loops, no summarization
    - Rule-first routing: Minimize LLM calls for known patterns
    - Cache-before-LLM: Check cache before any expensive operation
    - RAM-hardened: All heavy operations wrapped with RAM safety
    """
    
    def __init__(self):
        self.intent_router = IntentRouter()
        self.wiki_retriever = WikiRetriever()
        self.adaptive_router = AdaptiveRouter()
        
        # Set up RAM hardener callbacks
        ram_hardener.set_callbacks(
            unload_callback=self._unload_model,
            cache_clear_callback=self._clear_volatile_cache
        )
        
        logfire.info("CompilerPipeline initialized")

    def _unload_model(self) -> None:
        """Callback to unload current model when RAM is critical."""
        logfire.info("Unloading current model due to RAM pressure")
        # In production, this would call ollama delete or similar
        # For now, we just log it
        pass

    def _clear_volatile_cache(self) -> None:
        """Callback to clear volatile cache items."""
        cache_manager.clear_volatile()

    @ram_safe(threshold_gb=1.8)
    def run(self, user_input: str, project_path: str) -> dict[str, Any]:
        """
        Execute the full pipeline for a given user input and project path.
        
        Returns a JSON plan or error dictionary.
        """
        pipeline_result = {
            "success": False,
            "plan": None,
            "error": None,
            "fallback": None,
            "cache_hit": False,
            "model_used": None,
            "latency_ms": 0
        }
        
        start_time = 0
        
        with logfire.span("CompilerPipeline.run", user_input=user_input[:50], project_path=project_path):
            try:
                # Step 1: Parse - Detect changes and get raw tree (mocked for now)
                raw_tree = self._parse_project(project_path)
                
                # Step 2: Compress - Truncate context to fit token limits
                compressed_context = compress_context(
                    f"{user_input}\n\nProject Structure:\n{raw_tree}",
                    max_tokens=512
                )
                
                # Step 3: Retrieve - Enrich with wiki snippets BEFORE LLM
                wiki_snippets = self.wiki_retriever.search(user_input, k=3)
                enriched_context = self._inject_wiki_context(compressed_context, wiki_snippets)
                
                # Step 4: Route - Classify intent to select schema
                intent_result = self.intent_router.classify(user_input)
                schema_class = intent_result["schema_class"]
                intent_type = intent_result["intent"]
                
                # Step 5: Check Cache - Return cached plan if available
                cache_params = {
                    "user_input": user_input,
                    "project_path": project_path,
                    "intent": intent_type
                }
                plan_hash = cache_manager.get_plan_hash(cache_params)
                cached_plan = cache_manager.get_plan(plan_hash)
                
                if cached_plan is not None:
                    logfire.info("Cache hit, returning cached plan")
                    pipeline_result["cache_hit"] = True
                    pipeline_result["plan"] = cached_plan
                    pipeline_result["success"] = True
                    return pipeline_result
                
                # Step 6: Generate - Call LLM with schema enforcement
                llm_result = self.adaptive_router.generate(
                    schema_class=schema_class,
                    context=enriched_context,
                    user_input=user_input
                )
                
                pipeline_result["model_used"] = llm_result.get("model_used")
                
                # Step 7: Validate - instructor already validated, but double-check
                if llm_result.get("error"):
                    pipeline_result["error"] = llm_result["error"]
                    pipeline_result["fallback"] = "safe_mode"
                    return pipeline_result
                
                plan = llm_result.get("response")
                
                # Step 8: Cache - Store the generated plan
                cache_manager.store_plan(plan_hash, plan)
                
                # Step 9: Execute - Mock tool harness execution
                execution_result = self._execute_plan(plan)
                
                pipeline_result["plan"] = plan
                pipeline_result["execution"] = execution_result
                pipeline_result["success"] = True
                
            except Exception as e:
                logfire.error("Pipeline execution failed", error=str(e))
                pipeline_result["error"] = str(e)
                pipeline_result["fallback"] = "safe_mode"
            
            # Calculate latency (simplified)
            import time
            pipeline_result["latency_ms"] = int((time.time() - start_time) * 1000) if start_time else 0
            
            return pipeline_result

    def _parse_project(self, project_path: str) -> str:
        """
        Parse the Godot project structure.
        In production, this would use tools/godot/ parsers.
        For now, returns a mock tree.
        """
        with logfire.span("CompilerPipeline._parse_project", path=project_path):
            # Check cache first
            cached_tree = cache_manager.get_parsed_tree(project_path)
            if cached_tree:
                return cached_tree
            
            # Mock implementation - in production this uses watchfiles + godot parsers
            tree_data = {
                "project_path": project_path,
                "files": [],
                "nodes": [],
                "signals": []
            }
            
            # Scan for .gd and .tscn files
            if os.path.exists(project_path):
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        if file.endswith(('.gd', '.tscn')):
                            filepath = os.path.join(root, file)
                            tree_data["files"].append(filepath)
            
            tree_str = str(tree_data)
            
            # Cache the parsed tree
            cache_manager.store_parsed_tree(project_path, tree_data)
            
            return tree_str

    def _inject_wiki_context(self, context: str, wiki_snippets: list[dict]) -> str:
        """Inject wiki snippets into the context for the LLM."""
        if not wiki_snippets:
            return context
        
        wiki_text = "\n\nRelevant Documentation:\n"
        for snippet in wiki_snippets:
            wiki_text += f"- {snippet.get('title', 'Unknown')}: {snippet.get('content', '')}\n"
        
        return context + wiki_text

    def _execute_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the generated plan.
        In production, this would call tools/godot/ to apply changes.
        For now, just logs the plan.
        """
        with logfire.span("CompilerPipeline._execute_plan"):
            logfire.info("Executing plan", action=plan.get("action"))
            # Mock execution
            return {"status": "executed", "changes_applied": 0}


# Global pipeline instance
pipeline = CompilerPipeline()
