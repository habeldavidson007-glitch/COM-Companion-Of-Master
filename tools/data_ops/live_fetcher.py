import os
import re
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Union
from urllib.parse import urlparse
import hashlib
import tempfile
import shutil

# Third-party imports (ensure these are in requirements.txt)
try:
    import requests
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
    HAS_WEB_DEPS = True
except ImportError:
    HAS_WEB_DEPS = False

try:
    import git
    HAS_GIT_DEPS = True
except ImportError:
    HAS_GIT_DEPS = False

from tools.data_ops.wiki_compiler import WikiCompiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveFetcher:
    """
    Real-Time Curated Ingestion Module.
    Fetches content from URLs, Local Files, or Git Repos, cleans it,
    and compiles it into the local Wiki knowledge base.
    
    Designed for low-RAM environments: streams data where possible,
    avoids loading massive files entirely into memory when feasible.
    """

    def __init__(self, raw_dir: str = "data/raw", wiki_dir: str = "data/wiki"):
        self.raw_dir = Path(raw_dir)
        self.wiki_dir = Path(wiki_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the compiler to handle the final ingestion
        # WikiCompiler uses data_dir as base, so we use parent of wiki_dir
        self.compiler = WikiCompiler(data_dir=str(self.wiki_dir.parent))
        
        if not HAS_WEB_DEPS:
            logger.warning("Web dependencies (requests, beautifulsoup4, markdownify) missing. Web fetching disabled.")
        if not HAS_GIT_DEPS:
            logger.warning("Git dependencies (gitpython) missing. Git fetching disabled.")

    def fetch(self, source: str, source_type: str = "auto", title: Optional[str] = None) -> Dict:
        """
        Main entry point. Fetches, cleans, and compiles a source.
        
        Args:
            source: URL, file path, or git repo URL.
            source_type: 'url', 'file', 'git', or 'auto'.
            title: Optional custom title for the wiki entry.
            
        Returns:
            Dict with status, message, and wiki_path if successful.
        """
        if source_type == "auto":
            source_type = self._detect_source_type(source)

        logger.info(f"Fetching source: {source} (Type: {source_type})")

        try:
            if source_type == "url":
                content, final_title = self._fetch_url(source)
            elif source_type == "file":
                content, final_title = self._fetch_file(source)
            elif source_type == "git":
                content, final_title = self._fetch_git(source)
            else:
                return {"status": "error", "message": f"Unsupported source type: {source_type}"}

            # Use provided title or extracted title
            wiki_title = title or final_title or self._generate_title_from_source(source)
            
            # Compile to Wiki
            wiki_path = self.compile_to_wiki(content, wiki_title, metadata={"source": source, "type": source_type})
            
            return {
                "status": "success",
                "message": f"Successfully ingested {source}",
                "wiki_path": str(wiki_path),
                "title": wiki_title
            }

        except Exception as e:
            logger.error(f"Failed to fetch {source}: {e}")
            return {"status": "error", "message": str(e)}

    def _detect_source_type(self, source: str) -> str:
        if source.startswith(("http://", "https://")):
            if "github.com" in source or source.endswith(".git"):
                return "git"
            return "url"
        elif Path(source).exists():
            return "file"
        elif source.endswith(".git"):
            return "git"
        return "url" # Default fallback

    # --- WEB FETCHING ---
    def _fetch_url(self, url: str) -> tuple[str, str]:
        if not HAS_WEB_DEPS:
            raise ImportError("Missing web dependencies. Install: pip install requests beautifulsoup4 markdownify")

        headers = {'User-Agent': 'COM-Bot/3.0 (Low-Resource Knowledge Gatherer)'}
        
        # Stream request to avoid loading huge binary blobs if not needed
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        
        # For HTML pages
        if 'text/html' in content_type:
            # Read content in chunks if very large, but for BS4 we usually need the whole text
            # Limiting to first 5MB to prevent RAM spikes on massive pages
            html_content = response.text[:5*1024*1024] 
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract Title
            title_tag = soup.find('title')
            title = title_tag.string.strip() if title_tag else "Untitled Web Page"
            
            # Clean: Remove scripts, styles, navs, footers
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
                
            # Convert to Markdown
            markdown_content = md(str(soup), heading_style="ATX")
            
            # Basic cleanup of excessive newlines
            markdown_content = re.sub(r'\n\s*\n', '\n\n', markdown_content)
            
            return markdown_content, title
            
        # For plain text or unknown types
        else:
            content = response.text[:5*1024*1024]
            return content, urlparse(url).netloc

    # --- LOCAL FILE FETCHING ---
    def _fetch_file(self, file_path: str) -> tuple[str, str]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Local file not found: {file_path}")
        
        # If already markdown or text, just read
        if path.suffix in ['.md', '.txt']:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, path.stem
        
        # If PDF, we need a parser (placeholder for low-resource constraint)
        # In a real low-RAM env, we might call an external tool or use pypdf
        if path.suffix == '.pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(str(path))
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return "\n".join(text), path.stem
            except ImportError:
                raise ImportError("PDF support requires 'pypdf'. Install: pip install pypdf")
        
        raise ValueError(f"Unsupported file type: {path.suffix}")

    # --- GIT REPO FETCHING ---
    def _fetch_git(self, repo_url: str) -> tuple[str, str]:
        if not HAS_GIT_DEPS:
            raise ImportError("Missing git dependencies. Install: pip install gitpython")
        
        # Create a temp directory for cloning to avoid polluting raw_dir
        temp_dir = tempfile.mkdtemp(prefix="com_git_")
        try:
            logger.info(f"Cloning repo to temp: {temp_dir}")
            repo = git.Repo.clone_from(repo_url, temp_dir, depth=1) # Shallow clone for speed/RAM
            
            # Strategy: Prioritize README.md, then docs/ folder
            content_parts = []
            title = "Git Repository: " + Path(repo_url).stem
            
            readme_path = Path(temp_dir) / "README.md"
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content_parts.append(f"# README Content\n\n{f.read()}")
            
            docs_dir = Path(temp_dir) / "docs"
            if docs_dir.exists():
                for md_file in docs_dir.rglob("*.md"):
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content_parts.append(f"\n# Doc: {md_file.name}\n\n{f.read()}")
            
            if not content_parts:
                raise ValueError("No README or docs found in repository.")
                
            return "\n---\n".join(content_parts), title
            
        finally:
            # Cleanup temp dir immediately to save space
            shutil.rmtree(temp_dir, ignore_errors=True)

    # --- COMPILATION ---
    def compile_to_wiki(self, content: str, title: str, metadata: Dict = None) -> Path:
        """
        Uses the existing WikiCompiler to ingest the cleaned content.
        Generates a unique ID based on content hash to prevent duplicates.
        """
        # Generate a safe, unique document ID
        doc_id = hashlib.md5(f"{title}{content[:100]}".encode()).hexdigest()[:12]
        safe_title = re.sub(r'[^\w\s-]', '', title)[:50] # Sanitize title
        filename = f"{safe_title}_{doc_id}"
        
        # Use the compiler's ingestion logic
        # Assuming WikiCompiler has a method like ingest_text or we simulate file creation
        # Here we directly create the file and update index to ensure compatibility
        
        wiki_file = self.wiki_dir / f"{filename}.md"
        
        # Construct final markdown with metadata header
        meta = metadata or {}
        header = f"---\ntitle: {title}\nsource: {meta.get('source', 'unknown')}\ntype: {meta.get('type', 'unknown')}\n---\n\n"
        final_content = header + content
        
        with open(wiki_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        # Update the index via the indexer
        self.compiler.indexer.add_document(
            doc_id=filename,
            title=title,
            content=content,
            metadata=meta
        )
        
        logger.info(f"Compiled to wiki: {wiki_file}")
        return wiki_file

    def _generate_title_from_source(self, source: str) -> str:
        if source.startswith("http"):
            return urlparse(source).netloc
        return Path(source).stem
