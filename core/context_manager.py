"""
COM v4 - Context Manager

Handles context compression, Wiki injection, and prompt assembly.
Critical for managing the limited context window of small models.
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation history."""
    role: str  # 'user' or 'assistant'
    content: str
    tokens: int = 0
    
    def __post_init__(self):
        if self.tokens == 0:
            # Rough token estimation: 1 token ≈ 4 characters
            self.tokens = len(self.content) // 4


@dataclass
class WikiChunk:
    """A chunk of knowledge from the compiled Wiki."""
    source: str
    content: str
    relevance_score: float = 0.0
    tokens: int = 0
    
    def __post_init__(self):
        if self.tokens == 0:
            self.tokens = len(self.content) // 4


class ContextManager:
    """
    Manages context window for small models (1.5B parameter range).
    
    Key features:
    1. Compresses conversation history when approaching context limits
    2. Dynamically injects relevant Wiki knowledge
    3. Assembles optimized prompts with proper structure
    
    This is essential for making small models perform beyond their size
    by ensuring they always have the most relevant information available.
    """
    
    # Configuration
    MAX_CONTEXT_TOKENS = 4096  # Match modelfile num_ctx
    COMPRESSION_THRESHOLD = 0.8  # Compress at 80% capacity
    MAX_WIKI_CHUNKS = 5
    WIKI_CHUNK_SIZE = 512  # Tokens per chunk
    
    def __init__(
        self,
        wiki_path: str = "knowledge/compiled_wiki",
        system_prompt_path: str = "config/system_prompt.txt",
        model_name: str = "com-v4-cognitive"
    ):
        """
        Initialize the context manager.
        
        Args:
            wiki_path: Path to compiled Wiki knowledge base
            system_prompt_path: Path to system prompt template
            model_name: Name of the model (for token estimation)
        """
        self.wiki_path = Path(wiki_path)
        self.system_prompt_path = Path(system_prompt_path)
        self.model_name = model_name
        
        # Conversation history as a deque for efficient rotation
        self.history: deque[ConversationTurn] = deque()
        
        # Current query being processed
        self.current_query: Optional[str] = None
        
        # Loaded system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Cached Wiki index for fast retrieval
        self._wiki_index: Optional[dict[str, list[WikiChunk]]] = None
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from file or use default."""
        if self.system_prompt_path.exists():
            return self.system_prompt_path.read_text(encoding="utf-8")
        
        # Default system prompt if file doesn't exist
        return """You are COM v4, a Cognitive Architecture assistant.
You MUST follow this thinking process for EVERY response:

1. FIRST: Generate a <thought> block analyzing the request
2. SECOND: Decide if you need tools or can respond directly
3. THIRD: Output your action in <action> JSON format
4. FOURTH: Include a <confidence> score (0.0-1.0)

NEVER skip the thought block. ALWAYS verify your reasoning.
If you're unsure, say so and explain what additional information you need."""
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        
        Uses a simple heuristic: ~4 characters per token for English.
        For production, use a proper tokenizer.
        """
        return len(text) // 4
    
    def _load_wiki_index(self) -> dict[str, list[WikiChunk]]:
        """
        Load or build the Wiki index from compiled chunks.
        
        Returns:
            Dictionary mapping topics to lists of WikiChunks
        """
        if self._wiki_index is not None:
            return self._wiki_index
        
        self._wiki_index = {}
        
        if not self.wiki_path.exists():
            logger.warning(f"Wiki path does not exist: {self.wiki_path}")
            return self._wiki_index
        
        # Load all JSON chunk files
        for chunk_file in self.wiki_path.glob("*.json"):
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunk_data = json.load(f)
                
                chunk = WikiChunk(
                    source=chunk_data.get("source", chunk_file.stem),
                    content=chunk_data.get("content", ""),
                    relevance_score=chunk_data.get("relevance_score", 0.5)
                )
                
                # Index by topic/category
                topic = chunk_data.get("topic", "general")
                if topic not in self._wiki_index:
                    self._wiki_index[topic] = []
                self._wiki_index[topic].append(chunk)
                
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load Wiki chunk {chunk_file}: {e}")
        
        return self._wiki_index
    
    def compress_history(self) -> str:
        """
        Compress old conversation turns when context is getting full.
        
        Strategy:
        - Keep the last 2 turns intact
        - Summarize older turns into a single summary block
        
        Returns:
            Compressed history as a string
        """
        if len(self.history) <= 2:
            # No compression needed
            return self._format_history()
        
        # Keep recent turns
        recent_turns = list(self.history)[-2:]
        old_turns = list(self.history)[:-2]
        
        # Create summary of old turns
        summary_parts = []
        for turn in old_turns:
            summary_parts.append(f"{turn.role}: {turn.content[:100]}...")
        
        summary = "Previous conversation summary:\n" + "\n".join(summary_parts)
        
        # Format recent turns normally
        recent_formatted = "\n".join([
            f"<{turn.role}>{turn.content}</{turn.role}>"
            for turn in recent_turns
        ])
        
        return f"<conversation_summary>\n{summary}\n</conversation_summary>\n\n{recent_formatted}"
    
    def _format_history(self) -> str:
        """Format the full conversation history as XML-like tags."""
        if not self.history:
            return ""
        
        formatted = []
        for turn in self.history:
            formatted.append(f"<{turn.role}>{turn.content}</{turn.role}>")
        
        return "\n".join(formatted)
    
    def _get_current_token_count(self) -> int:
        """Calculate current token usage from history."""
        total = self._estimate_tokens(self.system_prompt)
        total += sum(turn.tokens for turn in self.history)
        return total
    
    def needs_compression(self) -> bool:
        """Check if context compression is needed."""
        current_usage = self._get_current_token_count()
        return current_usage > (self.MAX_CONTEXT_TOKENS * self.COMPRESSION_THRESHOLD)
    
    def inject_wiki_context(self, query: str) -> list[WikiChunk]:
        """
        Find and inject relevant Wiki chunks based on the query.
        
        Uses simple keyword matching. For production, replace with
        vector similarity search using embeddings.
        
        Args:
            query: Current user query
            
        Returns:
            List of relevant WikiChunk objects
        """
        wiki_index = self._load_wiki_index()
        
        if not wiki_index:
            return []
        
        # Simple keyword-based retrieval
        query_keywords = set(query.lower().split())
        relevant_chunks: list[WikiChunk] = []
        
        for topic, chunks in wiki_index.items():
            # Check if topic matches query keywords
            topic_match = any(kw in topic.lower() for kw in query_keywords)
            
            if topic_match:
                relevant_chunks.extend(chunks[:self.WIKI_CHUNK_SIZE])
        
        # Also search chunk content for keywords
        if len(relevant_chunks) < self.MAX_WIKI_CHUNKS:
            for topic, chunks in wiki_index.items():
                for chunk in chunks:
                    if any(kw in chunk.content.lower() for kw in query_keywords):
                        if chunk not in relevant_chunks:
                            relevant_chunks.append(chunk)
                            if len(relevant_chunks) >= self.MAX_WIKI_CHUNKS:
                                break
        
        # Limit to max chunks
        return relevant_chunks[:self.MAX_WIKI_CHUNKS]
    
    def _format_wiki_context(self, chunks: list[WikiChunk]) -> str:
        """Format Wiki chunks for injection into the prompt."""
        if not chunks:
            return ""
        
        formatted = ["<wiki_context>"]
        for i, chunk in enumerate(chunks, 1):
            formatted.append(f"<chunk_{i} source=\"{chunk.source}\">")
            formatted.append(chunk.content)
            formatted.append(f"</chunk_{i}>")
        formatted.append("</wiki_context>")
        
        return "\n".join(formatted)
    
    def add_turn(self, role: str, content: str) -> None:
        """
        Add a conversation turn to history.
        
        Args:
            role: 'user' or 'assistant'
            content: The message content
        """
        turn = ConversationTurn(role=role, content=content)
        self.history.append(turn)
        
        # Auto-compress if needed
        if self.needs_compression():
            logger.info("Context threshold reached, triggering compression")
            # Compression happens during prompt building
    
    def build_prompt(
        self,
        query: str,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Assemble the final prompt with all components.
        
        Structure:
        1. System prompt (personality and instructions)
        2. Wiki context (relevant knowledge)
        3. Conversation history (compressed if needed)
        4. Additional context (reflections, observations)
        5. Current query
        
        Args:
            query: Current user query
            additional_context: Optional extra context (reflections, etc.)
            
        Returns:
            Complete prompt string ready for model generation
        """
        self.current_query = query
        
        # Start with system prompt
        prompt_parts = [f"<system>{self.system_prompt}</system>"]
        
        # Inject Wiki context
        wiki_chunks = self.inject_wiki_context(query)
        if wiki_chunks:
            wiki_context = self._format_wiki_context(wiki_chunks)
            prompt_parts.append(wiki_context)
        
        # Add conversation history (compressed if needed)
        if self.needs_compression():
            history_str = self.compress_history()
        else:
            history_str = self._format_history()
        
        if history_str:
            prompt_parts.append(f"<conversation_history>\n{history_str}\n</conversation_history>")
        
        # Add additional context (reflections, tool observations)
        if additional_context:
            prompt_parts.append(f"<context>{additional_context}</context>")
        
        # Add current query
        prompt_parts.append(f"<user_query>{query}</user_query>")
        
        # Final instruction reminder
        prompt_parts.append("""
<instructions>
Remember to:
1. Think step-by-step in <thought> tags
2. Use tools when needed via <action> JSON
3. Report confidence in <confidence> tags
4. Reflect on errors before retrying
</instructions>""")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Log token estimate
        token_estimate = self._estimate_tokens(full_prompt)
        logger.info(f"Built prompt with ~{token_estimate} tokens")
        
        if token_estimate > self.MAX_CONTEXT_TOKENS:
            logger.warning(f"Prompt exceeds context limit ({token_estimate}/{self.MAX_CONTEXT_TOKENS})")
        
        return full_prompt
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.history.clear()
        self.current_query = None
        logger.info("Conversation history cleared")
    
    def get_stats(self) -> dict[str, Any]:
        """Get context management statistics."""
        return {
            "history_turns": len(self.history),
            "current_tokens": self._get_current_token_count(),
            "max_tokens": self.MAX_CONTEXT_TOKENS,
            "compression_needed": self.needs_compression(),
            "wiki_chunks_loaded": sum(
                len(chunks) for chunks in self._load_wiki_index().values()
            ) if self._wiki_index else 0
        }
