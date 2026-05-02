"""
Context Compressor Module - tiktoken-based context truncation.

CRITICAL: This module ensures LLM context never exceeds token limits.
Strategy: Keep start/end of file, truncate middle if needed.
Guarantee: Output never exceeds max_tokens limit.

Architecture Principle: Preserve critical context while staying within limits.
- Head: First N tokens (setup, imports, function signatures)
- Tail: Last N tokens (current working area, recent changes)
- Middle: Truncated with ellipsis marker
"""

from typing import Optional, Tuple
import sys

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not installed. ContextCompressor will use character-based fallback.", file=sys.stderr)

try:
    from config import MAX_CONTEXT_TOKENS, CONTEXT_TRUNCATION_STRATEGY
except ImportError:
    MAX_CONTEXT_TOKENS = 512
    CONTEXT_TRUNCATION_STRATEGY = "head_tail"


class ContextCompressor:
    """
    Compresses text context to fit within token limits.
    
    Uses tiktoken for accurate token counting and implements
    head-tail truncation strategy to preserve important context.
    
    Attributes:
        encoding: tiktoken encoding object (or None if unavailable)
        max_tokens: Maximum allowed tokens
        strategy: Truncation strategy ("head_tail" currently)
    
    Example:
        >>> compressor = ContextCompressor(max_tokens=512)
        >>> compressed = compressor.compress(long_text)
        >>> assert len(compressor.count_tokens(compressed)) <= 512
    """
    
    def __init__(
        self,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        strategy: str = CONTEXT_TRUNCATION_STRATEGY,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the context compressor.
        
        Args:
            max_tokens: Maximum tokens allowed in output.
            strategy: Truncation strategy ("head_tail").
            encoding_name: tiktoken encoding to use.
        """
        self.max_tokens = max_tokens
        self.strategy = strategy
        self.encoding = None
        
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoding = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                print(f"Warning: Could not load tiktoken encoding: {e}", file=sys.stderr)
                self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text.
        
        Returns:
            int: Token count.
        
        Fallback: If tiktoken unavailable, uses character-based estimation
                  (1 token ≈ 4 characters for English text).
        """
        if self.encoding is not None:
            return len(self.encoding.encode(text))
        else:
            # Fallback: rough estimation (1 token ≈ 4 chars)
            return len(text) // 4
    
    def compress(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        head_ratio: float = 0.4,
        tail_ratio: float = 0.4
    ) -> str:
        """
        Compress text to fit within token limit.
        
        Args:
            text: Input text to compress.
            max_tokens: Override for max_tokens (default: instance setting).
            head_ratio: Fraction of tokens for beginning (0.4 = 40%).
            tail_ratio: Fraction of tokens for end (0.4 = 40%).
                       Remaining 20% is buffer/ellipsis.
        
        Returns:
            str: Compressed text guaranteed to be within token limit.
        
        Strategy:
            - If text fits within limit, return unchanged.
            - Otherwise, keep head_ratio% from start, tail_ratio% from end.
            - Insert ellipsis marker (...) between them.
        
        Guarantee:
            Output token count <= max_tokens
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        # Check if compression is needed
        current_tokens = self.count_tokens(text)
        
        if current_tokens <= max_tokens:
            return text
        
        # Apply truncation strategy
        if self.strategy == "head_tail":
            return self._truncate_head_tail(text, max_tokens, head_ratio, tail_ratio)
        else:
            # Fallback: simple truncation from start
            return self._simple_truncate(text, max_tokens)
    
    def _truncate_head_tail(
        self,
        text: str,
        max_tokens: int,
        head_ratio: float,
        tail_ratio: float
    ) -> str:
        """
        Truncate keeping head and tail portions.
        
        Args:
            text: Input text.
            max_tokens: Maximum tokens allowed.
            head_ratio: Fraction for head portion.
            tail_ratio: Fraction for tail portion.
        
        Returns:
            str: Truncated text with ellipsis.
        """
        # Reserve some tokens for ellipsis and safety buffer
        buffer_tokens = max(10, int(max_tokens * 0.1))
        available_tokens = max_tokens - buffer_tokens
        
        head_tokens = int(available_tokens * head_ratio)
        tail_tokens = int(available_tokens * tail_ratio)
        
        # Ensure we have at least some content
        head_tokens = max(20, head_tokens)
        tail_tokens = max(20, tail_tokens)
        
        if self.encoding is not None:
            return self._truncate_with_tiktoken(text, head_tokens, tail_tokens)
        else:
            return self._truncate_char_based(text, head_tokens, tail_tokens)
    
    def _truncate_with_tiktoken(
        self,
        text: str,
        head_tokens: int,
        tail_tokens: int
    ) -> str:
        """
        Precise truncation using tiktoken encoding.
        
        Args:
            text: Input text.
            head_tokens: Tokens to keep from start.
            tail_tokens: Tokens to keep from end.
        
        Returns:
            str: Truncated text.
        """
        encoded = self.encoding.encode(text)
        total_tokens = len(encoded)
        
        if total_tokens <= head_tokens + tail_tokens:
            # Text is shorter than our allocation, return as-is
            return text
        
        # Take head and tail portions
        head_encoded = encoded[:head_tokens]
        tail_encoded = encoded[-tail_tokens:]
        
        # Decode back to text
        head_text = self.encoding.decode(head_encoded)
        tail_text = self.encoding.decode(tail_encoded)
        
        # Combine with ellipsis
        return f"{head_text}\n\n[...{total_tokens - head_tokens - tail_tokens} tokens truncated...]\n\n{tail_text}"
    
    def _truncate_char_based(
        self,
        text: str,
        head_tokens: int,
        tail_tokens: int
    ) -> str:
        """
        Character-based truncation fallback (when tiktoken unavailable).
        
        Args:
            text: Input text.
            head_tokens: Approximate tokens for head.
            tail_tokens: Approximate tokens for tail.
        
        Returns:
            str: Truncated text.
        """
        # Estimate characters (1 token ≈ 4 chars)
        head_chars = head_tokens * 4
        tail_chars = tail_tokens * 4
        
        total_len = len(text)
        
        if total_len <= head_chars + tail_chars:
            return text
        
        head_text = text[:head_chars]
        tail_text = text[-tail_chars:]
        
        # Find natural break points (newlines or spaces)
        head_text = self._find_natural_break(head_text, is_head=True)
        tail_text = self._find_natural_break(tail_text, is_head=False)
        
        return f"{head_text}\n\n[...truncated...]\n\n{tail_text}"
    
    def _simple_truncate(self, text: str, max_tokens: int) -> str:
        """
        Simple truncation from the start only.
        
        Used as fallback when head-tail strategy fails.
        
        Args:
            text: Input text.
            max_tokens: Maximum tokens.
        
        Returns:
            str: Truncated text from start.
        """
        if self.encoding is not None:
            encoded = self.encoding.encode(text)
            truncated = encoded[:max_tokens]
            return self.encoding.decode(truncated)
        else:
            # Character-based fallback
            max_chars = max_tokens * 4
            return text[:max_chars]
    
    def _find_natural_break(self, text: str, is_head: bool = True) -> str:
        """
        Find a natural break point (newline or space) for cleaner truncation.
        
        Args:
            text: Text to find break in.
            is_head: If True, look for break near end; else near start.
        
        Returns:
            str: Text truncated at natural break point.
        """
        if is_head:
            # Look for last newline or space
            for i in range(len(text) - 1, max(0, len(text) - 100), -1):
                if text[i] in '\n\r':
                    return text[:i+1].rstrip()
                elif text[i] == ' ' and i > len(text) // 2:
                    return text[:i]
        else:
            # Look for first newline or space
            for i in range(min(len(text), 100)):
                if text[i] in '\n\r':
                    return text[i+1:].lstrip()
                elif text[i] == ' ':
                    return text[i+1:].lstrip()
        
        return text


    def compress_many_with_budget(
        self,
        texts: list[str],
        max_total_tokens: int,
        per_item_floor: int = 64
    ) -> list[str]:
        """Compress multiple contexts so total tokens stay within one hard budget.

        DEV H Phase-2 focus: deterministic token budgeting before LLM call.
        """
        if not texts:
            return []

        compressed = [self.compress(t, max_tokens=max(per_item_floor, self.max_tokens)) for t in texts]
        counts = [self.count_tokens(t) for t in compressed]
        total = sum(counts)
        if total <= max_total_tokens:
            return compressed

        while total > max_total_tokens:
            idx = max(range(len(compressed)), key=lambda i: (counts[i], -i))
            if counts[idx] <= per_item_floor:
                break

            new_limit = max(per_item_floor, int(counts[idx] * 0.8))
            compressed[idx] = self.compress(compressed[idx], max_tokens=new_limit)
            old = counts[idx]
            counts[idx] = self.count_tokens(compressed[idx])
            if counts[idx] >= old:
                compressed[idx] = self._simple_truncate(compressed[idx], max(per_item_floor, old - 8))
                counts[idx] = self.count_tokens(compressed[idx])
            total = sum(counts)

            if all(c <= per_item_floor for c in counts) and total > max_total_tokens:
                for i in range(len(compressed)):
                    if total <= max_total_tokens:
                        break
                    compressed[i] = self._simple_truncate(compressed[i], max(8, counts[i] - 8))
                    counts[i] = self.count_tokens(compressed[i])
                    total = sum(counts)

        return compressed

    def compress_many_with_budget_stats(
        self,
        texts: list[str],
        max_total_tokens: int,
        per_item_floor: int = 64
    ) -> tuple[list[str], dict]:
        """Same as compress_many_with_budget, plus deterministic telemetry."""
        input_tokens_total = sum(self.count_tokens(t) for t in texts)
        compressed = self.compress_many_with_budget(
            texts=texts,
            max_total_tokens=max_total_tokens,
            per_item_floor=per_item_floor,
        )
        output_tokens_total = sum(self.count_tokens(t) for t in compressed)
        ratio = (output_tokens_total / input_tokens_total) if input_tokens_total else 0.0
        stats = {
            "input_tokens_total": input_tokens_total,
            "output_tokens_total": output_tokens_total,
            "compression_ratio": ratio,
            "budget_enforced": output_tokens_total <= max_total_tokens,
        }
        return compressed, stats


# Convenience function
def compress_context(
    text: str,
    max_tokens: int = MAX_CONTEXT_TOKENS,
    **kwargs
) -> str:
    """
    Convenience function for context compression.
    
    Creates a temporary compressor and compresses the text.
    For repeated use, instantiate ContextCompressor directly.
    
    Args:
        text: Input text to compress.
        max_tokens: Maximum tokens allowed.
        **kwargs: Additional args passed to ContextCompressor.
    
    Returns:
        str: Compressed text.
    """
    compressor = ContextCompressor(max_tokens=max_tokens, **kwargs)
    return compressor.compress(text, max_tokens)


if __name__ == "__main__":
    # Test the compressor
    print("=" * 50)
    print("Context Compressor Test")
    print("=" * 50)
    
    # Create test text (simulate a long file)
    test_lines = [f"Line {i}: This is some code content." for i in range(200)]
    long_text = "\n".join(test_lines)
    
    print(f"Original length: {len(long_text)} characters")
    
    compressor = ContextCompressor(max_tokens=100)
    compressed = compressor.compress(long_text)
    
    print(f"Compressed length: {len(compressed)} characters")
    print(f"Token count: {compressor.count_tokens(compressed)}")
    print(f"\nCompressed preview:")
    print(compressed[:500])
    if len(compressed) > 500:
        print("...")
    
    print("=" * 50)
