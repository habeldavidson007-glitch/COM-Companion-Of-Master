"""
Wiki Retriever Module - TF-IDF search for Godot documentation.

CRITICAL: This module enriches context BEFORE the LLM call to prevent hallucination.
It retrieves relevant wiki snippets that provide factual information about Godot APIs,
nodes, and patterns.

Architecture Principle: Zero Hallucination
- Structural facts come from parsing (watchfiles, regex)
- API facts come from wiki retrieval
- LLM only interprets and combines, never invents

Method: search(query, k=3) returns top 3 relevant docs/snippets.
"""

from typing import List, Dict, Optional, Tuple
import re
from collections import defaultdict
import math


class WikiRetriever:
    """
    TF-IDF based retriever for Godot documentation.
    
    This class builds an inverted index over documents and ranks them
    by TF-IDF similarity to a query. It's designed to be lightweight
    and work without external dependencies.
    
    Attributes:
        documents: Dict mapping doc_id to document text.
        idf_scores: Pre-computed IDF scores for terms.
        indexed: Whether the index has been built.
    
    Example:
        >>> retriever = WikiRetriever()
        >>> retriever.add_document("get_node", "Gets a node by path...")
        >>> results = retriever.search("find node path", k=3)
        >>> print(results[0]['doc_id'])
        'get_node'
    """
    
    def __init__(self):
        """Initialize the wiki retriever."""
        self.documents: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.term_freq: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.doc_freq: Dict[str, int] = defaultdict(int)
        self.idf_scores: Dict[str, float] = {}
        self.indexed = False
        self.total_docs = 0
    
    def add_document(self, doc_id: str, text: str) -> None:
        """
        Add a document to the corpus.
        
        Args:
            doc_id: Unique identifier for the document.
            text: Document content.
        
        Note:
            Call build_index() after adding all documents.
        """
        self.documents[doc_id] = text
        self.indexed = False
    
    def add_documents(self, docs: Dict[str, str]) -> None:
        """
        Add multiple documents at once.
        
        Args:
            docs: Dict mapping doc_id to text.
        """
        for doc_id, text in docs.items():
            self.add_document(doc_id, text)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into lowercase words.
        
        Args:
            text: Input text.
        
        Returns:
            List of lowercase word tokens.
        """
        # Convert to lowercase and extract words
        text = text.lower()
        tokens = re.findall(r'\b[a-z_][a-z0-9_]*\b', text)
        return tokens
    
    def build_index(self) -> None:
        """
        Build the TF-IDF index.
        
        Computes term frequencies and IDF scores for all documents.
        Must be called before search().
        """
        if self.indexed:
            return
        
        # Reset indices
        self.term_freq = defaultdict(lambda: defaultdict(int))
        self.doc_freq = defaultdict(int)
        self.doc_lengths = {}
        self.total_docs = len(self.documents)
        
        # Compute term frequencies
        for doc_id, text in self.documents.items():
            tokens = self._tokenize(text)
            self.doc_lengths[doc_id] = len(tokens)
            
            seen_terms = set()
            for token in tokens:
                self.term_freq[doc_id][token] += 1
                if token not in seen_terms:
                    self.doc_freq[token] += 1
                    seen_terms.add(token)
        
        # Compute IDF scores
        for term, df in self.doc_freq.items():
            # IDF = log(N / df) + 1 (smoothed)
            self.idf_scores[term] = math.log(self.total_docs / (df + 1)) + 1
        
        self.indexed = True
    
    def _compute_tf_idf(self, doc_id: str, query_terms: List[str]) -> float:
        """
        Compute TF-IDF score for a document given query terms.
        
        Args:
            doc_id: Document identifier.
            query_terms: Query tokens.
        
        Returns:
            float: TF-IDF similarity score.
        """
        if doc_id not in self.documents:
            return 0.0
        
        score = 0.0
        doc_len = self.doc_lengths.get(doc_id, 1)
        
        for term in query_terms:
            tf = self.term_freq[doc_id].get(term, 0)
            idf = self.idf_scores.get(term, 0)
            
            if tf > 0 and idf > 0:
                # Normalized TF * IDF
                normalized_tf = tf / doc_len
                score += normalized_tf * idf
        
        return score
    
    def search(
        self,
        query: str,
        k: int = 3
    ) -> List[Dict[str, any]]:
        """
        Search for documents matching the query.
        
        Args:
            query: Search query string.
            k: Number of results to return (default: 3).
        
        Returns:
            List of result dicts with 'doc_id', 'text', 'score' keys.
            Empty list if no matches or index not built.
        
        Critical:
            This runs BEFORE the LLM call to enrich context.
            Results are sorted by relevance (highest first).
        """
        if not self.indexed:
            self.build_index()
        
        if not self.documents:
            return []
        
        # Tokenize query
        query_terms = self._tokenize(query)
        
        if not query_terms:
            return []
        
        # Score all documents
        scores = []
        for doc_id in self.documents:
            score = self._compute_tf_idf(doc_id, query_terms)
            if score > 0:
                scores.append((doc_id, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k results
        results = []
        for doc_id, score in scores[:k]:
            results.append({
                "doc_id": doc_id,
                "text": self.documents[doc_id],
                "score": score
            })
        
        return results
    
    def get_snippets(
        self,
        query: str,
        k: int = 3,
        snippet_size: int = 200
    ) -> List[str]:
        """
        Get text snippets for context enrichment.
        
        Args:
            query: Search query.
            k: Number of snippets.
            snippet_size: Max characters per snippet.
        
        Returns:
            List of text snippets (truncated document content).
        
        Use Case:
            Pass these snippets to the LLM as context before asking
            it to explain errors or validate paths.
        """
        results = self.search(query, k)
        snippets = []
        
        for result in results:
            text = result["text"]
            if len(text) > snippet_size:
                # Truncate at word boundary
                truncated = text[:snippet_size]
                last_space = truncated.rfind(' ')
                if last_space > snippet_size // 2:
                    truncated = truncated[:last_space]
                text = truncated + "..."
            
            snippets.append(f"[{result['doc_id']}]: {text}")
        
        return snippets


# Default Godot wiki snippets for common operations
DEFAULT_GODOT_DOCS = {
    "get_node": """
@GDScript.get_node
Gets a node by path. The path can be absolute (starting with /) or relative.
Returns null if the node doesn't exist. Use has_node() to check first.
Example: var player = get_node("Player")
""",
    "SceneTree": """
Class: SceneTree
The main scene tree. Access via get_tree().
Methods: change_scene(), reload_current_scene(), quit()
Signals: tree_changed(), tree_exiting()
""",
    "Node Lifecycle": """
Node lifecycle: _ready() called when node enters tree.
_ready() is called once. _process() called every frame.
Use queue_free() to remove nodes safely.
""",
    "Signals": """
Signals are notifications emitted by nodes.
Connect via: node.signal.connect(callable)
Emit via: signal_name.emit()
Built-in signals: pressed, entered_tree, exited_tree
""",
    "Error Null Instance": """
"Attempt to call function on null instance" means:
1. The variable is null/uninitialized
2. The node was freed/deleted
3. The node path is wrong
Fix: Check with 'if node != null' before calling
""",
}


def create_default_retriever() -> WikiRetriever:
    """
    Create a retriever pre-loaded with default Godot docs.
    
    Returns:
        WikiRetriever: Ready-to-use retriever instance.
    """
    retriever = WikiRetriever()
    retriever.add_documents(DEFAULT_GODOT_DOCS)
    retriever.build_index()
    return retriever


# Convenience function
def search_wiki(query: str, k: int = 3) -> List[Dict[str, any]]:
    """
    Search the default Godot wiki.
    
    Args:
        query: Search query.
        k: Number of results.
    
    Returns:
        List of matching documents.
    """
    retriever = create_default_retriever()
    return retriever.search(query, k)


if __name__ == "__main__":
    # Test the retriever
    print("=" * 50)
    print("Wiki Retriever Test")
    print("=" * 50)
    
    retriever = create_default_retriever()
    
    # Test search
    query = "get node path"
    results = retriever.search(query, k=3)
    
    print(f"Query: '{query}'")
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['doc_id']}] (score: {result['score']:.4f})")
        print(f"   {result['text'][:100]}...")
        print()
    
    # Test snippets
    print("\nSnippets:")
    snippets = retriever.get_snippets("null instance error", k=2)
    for snippet in snippets:
        print(f"  {snippet}")
    
    print("=" * 50)
