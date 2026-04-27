"""
Wiki Retriever - TF-IDF based search for wiki content.
No embeddings, no external models - just pure term frequency.
"""
import re
from typing import Dict, List, Tuple, Any
from collections import Counter
from math import log10

from ..tools.safe_io import SafeIO


class WikiRetriever:
    """Simple TF-IDF retriever for wiki snippets."""
    
    def __init__(self, data_dir: str):
        self.io = SafeIO(data_dir)
        self.documents: Dict[str, str] = {}  # path -> content
        self.idf: Dict[str, float] = {}
        self._loaded = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, remove punctuation."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z]+\b', text)
        # Remove common stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose'
        }
        return [t for t in tokens if t not in stopwords and len(t) > 2]
    
    def load_wiki(self) -> None:
        """Load all wiki markdown files."""
        self.documents = {}
        
        try:
            md_files = self.io.list_files("wiki", "*.md")
            
            for path in md_files:
                if path == "wiki/_index.md":  # Skip index if exists
                    continue
                
                try:
                    content = self.io.read_text(path)
                    # Store first 2000 chars for speed (adjust as needed)
                    self.documents[path] = content[:2000]
                except Exception:
                    continue
            
            self._compute_idf()
            self._loaded = True
            
        except Exception:
            self._loaded = False
    
    def _compute_idf(self) -> None:
        """Compute IDF scores for all terms."""
        if not self.documents:
            return
        
        n_docs = len(self.documents)
        doc_freq: Counter = Counter()
        
        # Count document frequency for each term
        for content in self.documents.values():
            tokens = set(self._tokenize(content))
            for token in tokens:
                doc_freq[token] += 1
        
        # Compute IDF: log(N / df)
        self.idf = {
            term: log10(n_docs / freq) if freq > 0 else 0
            for term, freq in doc_freq.items()
        }
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """
        Search wiki for query.
        Returns list of (path, snippet, score).
        """
        if not self._loaded:
            self.load_wiki()
        
        if not self.documents:
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scores: Dict[str, float] = {}
        
        # Compute TF-IDF score for each document
        for path, content in self.documents.items():
            doc_tokens = self._tokenize(content)
            if not doc_tokens:
                continue
            
            # Term frequency in document
            tf = Counter(doc_tokens)
            max_tf = max(tf.values()) if tf else 1
            
            # Compute score
            score = 0.0
            for token in query_tokens:
                if token in tf and token in self.idf:
                    # Normalized TF * IDF
                    score += (tf[token] / max_tf) * self.idf[token]
            
            if score > 0:
                scores[path] = score
        
        # Sort by score descending
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Return with snippets
        results = []
        for path, score in sorted_results:
            content = self.documents[path]
            # Extract relevant snippet (first 200 chars for preview)
            snippet = content[:200].replace("\n", " ").strip() + "..."
            results.append((path, snippet, score))
        
        return results
    
    def get_related(self, path: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Find documents related to a given document."""
        if not self._loaded:
            self.load_wiki()
        
        if path not in self.documents:
            return []
        
        # Use document's own tokens as query
        content = self.documents[path]
        tokens = self._tokenize(content)
        
        # Get top terms in this document
        term_freq = Counter(tokens)
        top_terms = [term for term, _ in term_freq.most_common(10)]
        
        # Search using top terms
        query = " ".join(top_terms)
        results = self.search(query, top_k=top_k + 1)
        
        # Filter out the original document
        return [(p, s) for p, _, s in results if p != path][:top_k]
