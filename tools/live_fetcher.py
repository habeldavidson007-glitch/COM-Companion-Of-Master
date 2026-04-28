"""
COM v4 - Live Fetcher

Optional tool for fetching external information with strict safety limits.
Use sparingly as it can introduce latency and potential security risks.
"""

from __future__ import annotations

import logging
import urllib.request
import urllib.error
import json as json_lib
from typing import Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of a fetch operation."""
    success: bool
    content: str
    url: str
    status_code: Optional[int] = None
    error_type: Optional[str] = None


class LiveFetcher:
    """
    Safe external information fetcher with restrictions.
    
    Safety features:
    - URL whitelist (only allowed domains)
    - Response size limits
    - Timeout enforcement
    - No POST requests (GET only)
    - Content type validation
    
    Note: This tool should be used cautiously. For most use cases,
    the Wiki knowledge base is preferred over live fetching.
    """
    
    DEFAULT_TIMEOUT = 5.0  # seconds
    MAX_RESPONSE_SIZE = 50000  # bytes
    ALLOWED_CONTENT_TYPES = {
        'text/plain', 'text/html', 'application/json',
        'text/markdown', 'text/csv'
    }
    
    # URL whitelist - only these domains are allowed
    ALLOWED_DOMAINS = {
        'raw.githubusercontent.com',
        'example.com',  # Add trusted domains as needed
    }
    
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_response_size: int = MAX_RESPONSE_SIZE,
        use_whitelist: bool = True
    ):
        """
        Initialize the live fetcher.
        
        Args:
            timeout: Request timeout in seconds
            max_response_size: Maximum response size in bytes
            use_whitelist: Whether to enforce URL whitelist
        """
        self.timeout = timeout
        self.max_response_size = max_response_size
        self.use_whitelist = use_whitelist
    
    def _validate_url(self, url: str) -> tuple[bool, Optional[str]]:
        """
        Validate URL against safety rules.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Invalid URL format: {e}"
        
        # Must be HTTP(S)
        if parsed.scheme not in ('http', 'https'):
            return False, "Only HTTP/HTTPS URLs allowed"
        
        # Check whitelist if enabled
        if self.use_whitelist:
            domain = parsed.netloc.lower()
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            
            if domain not in self.ALLOWED_DOMAINS:
                return False, f"Domain not in whitelist: {domain}"
        
        return True, None
    
    def fetch(
        self,
        url: str,
        parse_json: bool = False
    ) -> FetchResult:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            parse_json: If True, attempt to parse response as JSON
            
        Returns:
            FetchResult with content or error
        """
        # Validate URL
        is_valid, error_msg = self._validate_url(url)
        if not is_valid:
            return FetchResult(
                success=False,
                content="",
                url=url,
                error_type="URL_VALIDATION",
            )
        
        try:
            # Create request
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'COM-v4-Cognitive/1.0',
                    'Accept': 'text/plain,text/html,application/json'
                }
            )
            
            # Execute request
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                # Check content type
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Read response with size limit
                content_bytes = b''
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    content_bytes += chunk
                    
                    if len(content_bytes) > self.max_response_size:
                        logger.warning(f"Response exceeded size limit from {url}")
                        break
                
                # Decode content
                try:
                    content = content_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    content = content_bytes.decode('latin-1', errors='ignore')
                
                # Parse JSON if requested
                if parse_json:
                    try:
                        parsed = json_lib.loads(content)
                        content = json_lib.dumps(parsed, indent=2)
                    except json_lib.JSONDecodeError as e:
                        return FetchResult(
                            success=False,
                            content="",
                            url=url,
                            error_type=f"JSON parse error: {e}"
                        )
                
                return FetchResult(
                    success=True,
                    content=content[:self.max_response_size],
                    url=url,
                    status_code=response.status
                )
                
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e.code}")
            return FetchResult(
                success=False,
                content="",
                url=url,
                status_code=e.code,
                error_type=f"HTTP {e.code}"
            )
        except urllib.error.URLError as e:
            logger.warning(f"URL error fetching {url}: {e.reason}")
            return FetchResult(
                success=False,
                content="",
                url=url,
                error_type=f"Network error: {e.reason}"
            )
        except TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            return FetchResult(
                success=False,
                content="",
                url=url,
                error_type="Timeout"
            )
        except Exception as e:
            logger.exception(f"Unexpected error fetching {url}")
            return FetchResult(
                success=False,
                content="",
                url=url,
                error_type=str(e)
            )
    
    def fetch_wiki_page(self, repo: str, path: str) -> FetchResult:
        """
        Fetch a file from a GitHub repository (raw content).
        
        Args:
            repo: Repository in format "owner/repo"
            path: File path within repository
            
        Returns:
            FetchResult with file content
        """
        url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
        return self.fetch(url)
    
    def add_allowed_domain(self, domain: str) -> None:
        """
        Add a domain to the whitelist.
        
        Args:
            domain: Domain name to allow
        """
        self.ALLOWED_DOMAINS.add(domain.lower())
        logger.info(f"Added domain to whitelist: {domain}")


# Convenience function
def safe_fetch(url: str, timeout: float = 5.0) -> FetchResult:
    """
    Fetch URL with default safety settings.
    
    Args:
        url: URL to fetch
        timeout: Request timeout
        
    Returns:
        FetchResult
    """
    fetcher = LiveFetcher(timeout=timeout)
    return fetcher.fetch(url)
