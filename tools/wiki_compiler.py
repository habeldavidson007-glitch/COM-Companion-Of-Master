"""
COM v4 - Wiki Compiler

Compiles raw knowledge files into structured, chunked format for efficient retrieval.
This is the "knowledge ingestion" pipeline that builds long-term memory.
"""

from __future__ import annotations

import os
import json
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeChunk:
    """A processed chunk of knowledge."""
    id: str
    source: str
    topic: str
    content: str
    metadata: dict[str, Any]
    created_at: str
    token_count: int = 0
    
    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = len(self.content) // 4
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "topic": self.topic,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "token_count": self.token_count
        }


class WikiCompiler:
    """
    Compiles raw knowledge files into structured chunks.
    
    Process:
    1. Read raw markdown/text files from knowledge/raw/
    2. Parse and split into logical chunks (by headers, sections)
    3. Extract topics and metadata
    4. Save as JSON files in knowledge/compiled_wiki/
    
    This enables the ContextManager to quickly retrieve relevant
    knowledge without reprocessing raw files every time.
    """
    
    CHUNK_SIZE_TARGET = 512  # Target tokens per chunk
    MAX_CHUNK_SIZE = 768  # Maximum tokens before forced split
    MIN_CHUNK_SIZE = 128  # Minimum tokens before merging
    
    def __init__(
        self,
        raw_path: str = "knowledge/raw",
        compiled_path: str = "knowledge/compiled_wiki"
    ):
        """
        Initialize the wiki compiler.
        
        Args:
            raw_path: Path to raw knowledge files
            compiled_path: Path to store compiled chunks
        """
        self.raw_path = Path(raw_path)
        self.compiled_path = Path(compiled_path)
        
        # Ensure output directory exists
        self.compiled_path.mkdir(parents=True, exist_ok=True)
    
    def compile_all(self, force: bool = False) -> list[KnowledgeChunk]:
        """
        Compile all raw files into chunks.
        
        Args:
            force: If True, recompile even if output already exists
            
        Returns:
            List of all compiled KnowledgeChunks
        """
        all_chunks = []
        
        if not self.raw_path.exists():
            logger.warning(f"Raw knowledge path does not exist: {self.raw_path}")
            self.raw_path.mkdir(parents=True, exist_ok=True)
            return all_chunks
        
        # Find all supported file types
        raw_files = list(self.raw_path.glob("*.md")) + \
                    list(self.raw_path.glob("*.txt")) + \
                    list(self.raw_path.glob("*.rst"))
        
        logger.info(f"Found {len(raw_files)} raw knowledge files")
        
        for raw_file in raw_files:
            chunks = self.compile_file(raw_file, force=force)
            all_chunks.extend(chunks)
        
        logger.info(f"Compiled {len(all_chunks)} total chunks")
        return all_chunks
    
    def compile_file(
        self,
        file_path: Path | str,
        force: bool = False
    ) -> list[KnowledgeChunk]:
        """
        Compile a single raw file into chunks.
        
        Args:
            file_path: Path to the raw file
            force: If True, recompile even if output exists
            
        Returns:
            List of KnowledgeChunks from this file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        # Check if already compiled
        output_file = self.compiled_path / f"{file_path.stem}.json"
        if output_file.exists() and not force:
            logger.debug(f"Skipping already compiled: {file_path.name}")
            return self._load_chunks(output_file)
        
        # Read and parse file
        content = file_path.read_text(encoding="utf-8")
        chunks = self._parse_and_chunk(content, file_path.stem)
        
        # Save chunks
        self._save_chunks(chunks, output_file)
        
        logger.info(f"Compiled {len(chunks)} chunks from {file_path.name}")
        return chunks
    
    def _parse_and_chunk(
        self,
        content: str,
        source_name: str
    ) -> list[KnowledgeChunk]:
        """
        Parse content and split into logical chunks.
        
        Strategy:
        - Split by markdown headers (##, ###, etc.)
        - Merge small chunks, split large ones
        - Extract topic from headers
        
        Args:
            content: Raw file content
            source_name: Name of the source file
            
        Returns:
            List of KnowledgeChunks
        """
        chunks = []
        current_topic = source_name
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for header
            if line.startswith('#'):
                # Save previous chunk if exists
                if current_content:
                    chunk = self._create_chunk(
                        content='\n'.join(current_content),
                        source=source_name,
                        topic=current_topic
                    )
                    if chunk:
                        chunks.append(chunk)
                
                # Extract new topic from header
                current_topic = line.lstrip('#').strip()
                current_content = [line]
            else:
                current_content.append(line)
        
        # Don't forget the last chunk
        if current_content:
            chunk = self._create_chunk(
                content='\n'.join(current_content),
                source=source_name,
                topic=current_topic
            )
            if chunk:
                chunks.append(chunk)
        
        # Post-process: merge small chunks, split large ones
        chunks = self._optimize_chunks(chunks)
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        source: str,
        topic: str
    ) -> Optional[KnowledgeChunk]:
        """
        Create a KnowledgeChunk from content.
        
        Args:
            content: Chunk content
            source: Source file name
            topic: Extracted topic
            
        Returns:
            KnowledgeChunk or None if too small
        """
        # Skip empty or very small chunks
        if len(content.strip()) < 50:
            return None
        
        # Generate unique ID
        chunk_id = hashlib.md5(
            f"{source}:{topic}:{content[:100]}".encode()
        ).hexdigest()[:12]
        
        # Extract metadata
        metadata = {
            "word_count": len(content.split()),
            "char_count": len(content)
        }
        
        return KnowledgeChunk(
            id=chunk_id,
            source=source,
            topic=topic,
            content=content.strip(),
            metadata=metadata,
            created_at=datetime.utcnow().isoformat()
        )
    
    def _optimize_chunks(
        self,
        chunks: list[KnowledgeChunk]
    ) -> list[KnowledgeChunk]:
        """
        Optimize chunks by merging small ones and splitting large ones.
        
        Args:
            chunks: Original chunks
            
        Returns:
            Optimized chunks
        """
        if not chunks:
            return chunks
        
        optimized = []
        buffer = []
        buffer_tokens = 0
        
        for chunk in chunks:
            chunk_tokens = chunk.token_count
            
            # If chunk is too large, split it
            if chunk_tokens > self.MAX_CHUNK_SIZE:
                # Flush buffer first
                if buffer:
                    merged = self._merge_chunks(buffer)
                    optimized.append(merged)
                    buffer = []
                    buffer_tokens = 0
                
                # Split large chunk
                split_chunks = self._split_chunk(chunk)
                optimized.extend(split_chunks)
                
            # If adding this chunk keeps us under target, add to buffer
            elif buffer_tokens + chunk_tokens <= self.CHUNK_SIZE_TARGET:
                buffer.append(chunk)
                buffer_tokens += chunk_tokens
                
            # Otherwise, flush buffer and start new one
            else:
                if buffer:
                    merged = self._merge_chunks(buffer)
                    optimized.append(merged)
                buffer = [chunk]
                buffer_tokens = chunk_tokens
        
        # Don't forget remaining buffer
        if buffer:
            merged = self._merge_chunks(buffer)
            optimized.append(merged)
        
        return optimized
    
    def _merge_chunks(self, chunks: list[KnowledgeChunk]) -> KnowledgeChunk:
        """Merge multiple chunks into one."""
        if len(chunks) == 1:
            return chunks[0]
        
        merged_content = '\n\n'.join(c.content for c in chunks)
        merged_topic = chunks[0].topic  # Use first chunk's topic
        
        return KnowledgeChunk(
            id=chunks[0].id,  # Keep first ID
            source=chunks[0].source,
            topic=merged_topic,
            content=merged_content,
            metadata={"merged_from": [c.id for c in chunks]},
            created_at=datetime.utcnow().isoformat()
        )
    
    def _split_chunk(self, chunk: KnowledgeChunk) -> list[KnowledgeChunk]:
        """Split a large chunk into smaller ones."""
        # Simple split by paragraphs
        paragraphs = chunk.content.split('\n\n')
        result = []
        current_parts = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = len(para) // 4
            
            if current_tokens + para_tokens <= self.CHUNK_SIZE_TARGET:
                current_parts.append(para)
                current_tokens += para_tokens
            else:
                if current_parts:
                    # Create new chunk
                    new_chunk = KnowledgeChunk(
                        id=f"{chunk.id}_part{len(result)+1}",
                        source=chunk.source,
                        topic=chunk.topic,
                        content='\n\n'.join(current_parts),
                        metadata={"split_from": chunk.id},
                        created_at=datetime.utcnow().isoformat()
                    )
                    result.append(new_chunk)
                current_parts = [para]
                current_tokens = para_tokens
        
        # Add remaining
        if current_parts:
            new_chunk = KnowledgeChunk(
                id=f"{chunk.id}_part{len(result)+1}",
                source=chunk.source,
                topic=chunk.topic,
                content='\n\n'.join(current_parts),
                metadata={"split_from": chunk.id},
                created_at=datetime.utcnow().isoformat()
            )
            result.append(new_chunk)
        
        return result if result else [chunk]
    
    def _save_chunks(
        self,
        chunks: list[KnowledgeChunk],
        output_file: Path
    ) -> None:
        """Save chunks to JSON file."""
        data = {
            "compiled_at": datetime.utcnow().isoformat(),
            "chunk_count": len(chunks),
            "chunks": [c.to_dict() for c in chunks]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_chunks(self, file_path: Path) -> list[KnowledgeChunk]:
        """Load chunks from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return [
                KnowledgeChunk(
                    id=c["id"],
                    source=c["source"],
                    topic=c["topic"],
                    content=c["content"],
                    metadata=c.get("metadata", {}),
                    created_at=c.get("created_at", "")
                )
                for c in data.get("chunks", [])
            ]
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load chunks from {file_path}: {e}")
            return []
    
    def clear_compiled(self) -> None:
        """Clear all compiled chunks."""
        for chunk_file in self.compiled_path.glob("*.json"):
            chunk_file.unlink()
        logger.info("Cleared all compiled chunks")


# Convenience function
def compile_wiki(
    raw_path: str = "knowledge/raw",
    compiled_path: str = "knowledge/compiled_wiki",
    force: bool = False
) -> list[KnowledgeChunk]:
    """
    Compile all wiki files.
    
    Args:
        raw_path: Path to raw files
        compiled_path: Path for compiled output
        force: Force recompilation
        
    Returns:
        List of compiled chunks
    """
    compiler = WikiCompiler(raw_path, compiled_path)
    return compiler.compile_all(force=force)
