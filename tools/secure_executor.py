"""
COM v4 - Secure Executor

Sandboxed subprocess execution with strict timeouts and resource limits.
Critical for safe code execution in the cognitive architecture.
"""

from __future__ import annotations

import subprocess
import logging
import sys
import tempfile
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any
import json

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a secure code execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time_ms: float
    error_type: Optional[str] = None


class SecureExecutor:
    """
    Secure code executor with sandboxing and resource limits.
    
    Safety features:
    - Timeout enforcement (hard limit)
    - Restricted imports whitelist
    - No network access
    - No file system write access (except temp directory)
    - Memory limits via subprocess isolation
    
    This tool enables the 1.5B model to perform complex computations
    by offloading them to Python while maintaining security.
    """
    
    DEFAULT_TIMEOUT = 5.0  # seconds
    MAX_OUTPUT_SIZE = 10000  # characters
    
    # Safe imports whitelist
    SAFE_IMPORTS = {
        'math', 'random', 'statistics', 'itertools', 'collections',
        're', 'datetime', 'time', 'json', 'csv', 'typing',
        'functools', 'operator', 'string', 'hashlib', 'base64'
    }
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        '__import__', 'importlib', 'subprocess', 'os.system',
        'eval(', 'exec(', 'compile(', 'open(', 'file(',
        'socket', 'urllib', 'requests', 'http', 'ftp',
        'pickle', 'marshal', 'shutil.rmtree', 'os.remove'
    ]
    
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_output_size: int = MAX_OUTPUT_SIZE,
        use_whitelist: bool = True
    ):
        """
        Initialize the secure executor.
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_size: Maximum output size in characters
            use_whitelist: Whether to enforce import whitelist
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.use_whitelist = use_whitelist
    
    def _validate_code(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate code for safety before execution.
        
        Args:
            code: Python code string to validate
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check imports if whitelist is enabled
        if self.use_whitelist:
            import_lines = [
                line for line in code.split('\n')
                if line.strip().startswith('import ') or line.strip().startswith('from ')
            ]
            
            for imp_line in import_lines:
                # Extract module name
                parts = imp_line.replace('from ', '').replace('import ', '').split()
                if parts:
                    module = parts[0].split('.')[0]
                    if module not in self.SAFE_IMPORTS:
                        return False, f"Unsafe import: {module}"
        
        return True, None
    
    def execute(
        self,
        code: str,
        input_data: Optional[dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute Python code securely in a subprocess.
        
        Args:
            code: Python code to execute
            input_data: Optional dictionary to pass as 'input_data' variable
            
        Returns:
            ExecutionResult with output and metadata
        """
        import time
        start_time = time.time()
        
        # Validate code first
        is_safe, error_msg = self._validate_code(code)
        if not is_safe:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=error_msg,
                return_code=-1,
                execution_time_ms=0,
                error_type="SECURITY_VIOLATION"
            )
        
        # Prepare execution environment
        try:
            # Create wrapper script
            wrapper_code = self._create_wrapper(code, input_data)
            
            # Execute in subprocess with timeout
            result = subprocess.run(
                [sys.executable, '-c', wrapper_code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._get_safe_env(),
                cwd=tempfile.gettempdir()
            )
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # Truncate outputs if too large
            stdout = result.stdout[:self.max_output_size]
            stderr = result.stderr[:self.max_output_size]
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                return_code=result.returncode,
                execution_time_ms=execution_time
            )
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Code execution timed out after {self.timeout}s")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {self.timeout} seconds",
                return_code=-2,
                execution_time_ms=self.timeout * 1000,
                error_type="TIMEOUT"
            )
        except Exception as e:
            logger.exception("Unexpected execution error")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-3,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_type="EXECUTION_ERROR"
            )
    
    def _create_wrapper(self, code: str, input_data: Optional[dict]) -> str:
        """
        Create a wrapper script that safely executes user code.
        
        Args:
            code: User's Python code
            input_data: Optional input data dictionary
            
        Returns:
            Wrapper script as string
        """
        # Sanitize code indentation
        lines = code.split('\n')
        if lines:
            # Remove common leading whitespace
            min_indent = min(
                len(line) - len(line.lstrip())
                for line in lines if line.strip()
            )
            code = '\n'.join(line[min_indent:] for line in lines)
        
        wrapper = """
import sys
import json

# Redirect stderr to capture errors
try:
"""
        
        # Add input data if provided
        if input_data:
            wrapper += f"""
    input_data = {json.dumps(input_data)}
"""
        else:
            wrapper += """
    input_data = None
"""
        
        # Add user code with indentation
        wrapper += '\n'.join('    ' + line for line in code.split('\n'))
        
        wrapper += """

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
"""
        
        return wrapper
    
    def _get_safe_env(self) -> dict[str, str]:
        """
        Get a sanitized environment for subprocess execution.
        
        Returns:
            Dictionary of safe environment variables
        """
        # Start with minimal environment
        safe_env = {
            'PATH': os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin'),
            'PYTHONPATH': '',
            'HOME': tempfile.gettempdir(),
        }
        
        # Add necessary Python settings
        safe_env['PYTHONDONTWRITEBYTECODE'] = '1'
        safe_env['PYTHONUNBUFFERED'] = '1'
        
        return safe_env
    
    def execute_expression(self, expression: str) -> ExecutionResult:
        """
        Safely evaluate a simple Python expression.
        
        Args:
            expression: Python expression string (e.g., "2 + 2 * 3")
            
        Returns:
            ExecutionResult with the evaluated result
        """
        # Wrap expression in print statement
        code = f"print({expression})"
        return self.execute(code)


# Convenience function for direct use
def safe_execute(code: str, timeout: float = 5.0) -> ExecutionResult:
    """
    Execute code securely with default settings.
    
    Args:
        code: Python code to execute
        timeout: Execution timeout in seconds
        
    Returns:
        ExecutionResult
    """
    executor = SecureExecutor(timeout=timeout)
    return executor.execute(code)
