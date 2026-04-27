"""
Python Expert Module for COM
Specialized in Python development, virtual environments, package management, and best practices.
"""

import os
import sys
import subprocess
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from tools.base import BaseTool

class PythonExpertTool(BaseTool):
    """Tool for Python development assistance."""
    
    def __init__(self):
        super().__init__()
        self.name = "PythonExpertTool"
        self.description = "Expert in Python development: code analysis, virtual environments, pip package management, PEP8 compliance, debugging, and automation scripts."
        self.pep8_common_issues = [
            "line too long",
            "undefined name",
            "unused variable",
            "import not at top",
            "multiple imports on one line",
            "missing whitespace",
            "unexpected indentation"
        ]
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute Python-related tasks.
        
        Actions:
        - 'analyze_code': Analyze Python code for issues and suggestions
        - 'check_dependencies': Check requirements.txt or pyproject.toml
        - 'suggest_fix': Suggest fixes for common Python errors
        - 'generate_template': Generate Python code templates
        - 'explain_concept': Explain Python concepts
        - 'run_safety_check': Check code for unsafe operations
        """
        if action == "analyze_code":
            return self.analyze_code(kwargs.get("code", ""))
        elif action == "check_dependencies":
            return self.check_dependencies(kwargs.get("file_path", "requirements.txt"))
        elif action == "suggest_fix":
            return self.suggest_fix(kwargs.get("error", ""), kwargs.get("code", ""))
        elif action == "generate_template":
            return self.generate_template(kwargs.get("template_type", "script"))
        elif action == "explain_concept":
            return self.explain_concept(kwargs.get("concept", ""))
        elif action == "run_safety_check":
            return self.run_safety_check(kwargs.get("code", ""))
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "analyze_code", "check_dependencies", "suggest_fix",
                "generate_template", "explain_concept", "run_safety_check"
            ]}
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze Python code for issues, best practices, and improvements."""
        issues = []
        suggestions = []
        strengths = []
        
        lines = code.splitlines()
        
        # Check for shebang
        if lines and lines[0].startswith('#!'):
            strengths.append("Has proper shebang line")
        
        # Check for docstring in functions/classes
        func_pattern = r'def\s+\w+'
        class_pattern = r'class\s+\w+'
        
        has_functions = bool(re.search(func_pattern, code))
        has_classes = bool(re.search(class_pattern, code))
        
        if has_functions and '"""' not in code and "'''" not in code:
            issues.append("Functions lack docstrings (PEP 257)")
        elif has_functions:
            strengths.append("Functions have docstrings")
        
        # Check for type hints
        type_hint_pattern = r'def\s+\w+\s*\([^)]*:\s*\w+'
        if has_functions and not re.search(type_hint_pattern, code):
            suggestions.append("Consider adding type hints for function parameters (PEP 484)")
        else:
            strengths.append("Uses type hints")
        
        # Check for print statements in production code
        if re.search(r'^\s*print\s*\(', code, re.MULTILINE):
            suggestions.append("Replace print() with logging module for production code")
        
        # Check for bare except clauses
        if re.search(r'except\s*:', code):
            issues.append("Bare 'except:' clause detected. Use specific exceptions (e.g., 'except ValueError:')")
        
        # Check for mutable default arguments
        mutable_default = re.search(r'def\s+\w+\s*\([^)]*=\s*(\[\]|\{\})', code)
        if mutable_default:
            issues.append("Mutable default argument detected. Use None and initialize inside function")
        
        # Check for global variables
        if re.search(r'^\s*global\s+', code, re.MULTILINE):
            suggestions.append("Minimize use of global variables. Consider using classes or closures")
        
        # Check for f-strings (Python 3.6+)
        if '.format(' in code and 'f"' not in code and "f'" not in code:
            suggestions.append("Consider using f-strings instead of .format() for better readability")
        
        # Check for proper if __name__ == "__main__"
        if has_functions and 'if __name__' not in code:
            if any('main' in line.lower() for line in lines):
                suggestions.append("Add 'if __name__ == \"__main__\":' guard for script entry point")
        else:
            strengths.append("Proper script entry point guard")
        
        # Check for context managers
        if 'open(' in code and 'with ' not in code:
            issues.append("Use 'with' statement for file operations (context manager)")
        
        # Count lines of code
        non_empty_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        return {
            "status": "analyzed",
            "issues": issues,
            "suggestions": suggestions,
            "strengths": strengths,
            "metrics": {
                "total_lines": len(lines),
                "non_empty_lines": non_empty_lines,
                "has_functions": has_functions,
                "has_classes": has_classes
            }
        }
    
    def check_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Check requirements.txt or pyproject.toml for issues."""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        ext = Path(file_path).suffix.lower()
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            dependencies = []
            issues = []
            
            if ext == '.txt':  # requirements.txt
                lines = content.splitlines()
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse package name and version
                    match = re.match(r'^([a-zA-Z0-9_-]+)([<>=!~]+.+)?$', line)
                    if match:
                        pkg_name = match.group(1)
                        version_spec = match.group(2)
                        
                        dependencies.append({
                            "package": pkg_name,
                            "version_spec": version_spec or "unspecified"
                        })
                        
                        if not version_spec:
                            issues.append(f"No version specified for {pkg_name}")
                    else:
                        issues.append(f"Invalid requirement format: {line}")
            
            elif ext == '.toml':  # pyproject.toml
                # Basic parsing (full TOML parsing would require tomllib)
                if '[project]' in content or '[tool.poetry]' in content:
                    dependencies.append({"note": "pyproject.toml detected - modern format"})
                else:
                    issues.append("pyproject.toml missing [project] or [tool.poetry] section")
            
            return {
                "success": True,
                "file": file_path,
                "dependencies": dependencies,
                "dependency_count": len(dependencies),
                "issues": issues,
                "recommendations": [
                    "Pin versions for reproducible builds",
                    "Use compatible release operator (~=) for libraries",
                    "Separate dev dependencies into requirements-dev.txt"
                ] if not issues else []
            }
            
        except Exception as e:
            return {"error": f"Failed to parse dependencies: {str(e)}"}
    
    def suggest_fix(self, error: str, code: str = "") -> Dict[str, Any]:
        """Suggest fixes for common Python errors."""
        error_lower = error.lower()
        
        fixes = []
        
        if "indentationerror" in error_lower:
            fixes.append({
                "issue": "Indentation Error",
                "solution": "Ensure consistent use of spaces (4 per level) or tabs. Mix is not allowed.",
                "example": "def func():\n    # Use 4 spaces, not tabs\n    pass"
            })
        
        if "nameerror" in error_lower or "undefined name" in error_lower:
            fixes.append({
                "issue": "NameError - Undefined Variable",
                "solution": "Check spelling, ensure variable is defined before use, or import the missing module.",
                "example": "# Before: prnt('hello')\n# After: print('hello')"
            })
        
        if "typeerror" in error_lower:
            fixes.append({
                "issue": "TypeError - Wrong Data Type",
                "solution": "Check operand types. Use str(), int(), float() for conversion if needed.",
                "example": "# Before: 'Age: ' + 25\n# After: 'Age: ' + str(25)"
            })
        
        if "importerror" in error_lower or "module not found" in error_lower:
            fixes.append({
                "issue": "ImportError - Module Not Found",
                "solution": "Install the package with pip, check spelling, or verify virtual environment.",
                "example": "pip install package_name\n# Or check: python -m pip list"
            })
        
        if "syntaxerror" in error_lower:
            fixes.append({
                "issue": "SyntaxError",
                "solution": "Check for missing colons, parentheses, quotes, or incorrect indentation.",
                "example": "# Before: if x > 5\n# After: if x > 5:"
            })
        
        if "attributeerror" in error_lower:
            fixes.append({
                "issue": "AttributeError",
                "solution": "Check object type, method spelling, or if the attribute exists.",
                "example": "# Before: my_list.appnd(1)\n# After: my_list.append(1)"
            })
        
        if not fixes:
            fixes.append({
                "issue": "General Error",
                "solution": "Read the full traceback, check line numbers, and search for the specific error message.",
                "example": "Use pdb or print() debugging to isolate the issue"
            })
        
        return {
            "original_error": error,
            "suggested_fixes": fixes,
            "general_advice": [
                "Read error messages from bottom to top",
                "Check the line number mentioned in traceback",
                "Use a linter like flake8 or pylint",
                "Run code with python -Wd to see deprecation warnings"
            ]
        }
    
    def generate_template(self, template_type: str) -> str:
        """Generate Python code templates for common use cases."""
        templates = {
            "script": '''#!/usr/bin/env python3
"""Module docstring describing the script's purpose."""

import argparse
import logging
import sys
from typing import Optional


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Script description here")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('--config', type=str, help="Path to configuration file")
    
    parsed_args = parser.parse_args(args)
    setup_logging(parsed_args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting script...")
    
    # Your code here
    
    logger.info("Script completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
            "class": '''class ClassName:
    """Class docstring explaining purpose and usage."""
    
    def __init__(self, param1: str, param2: int = 0) -> None:
        """Initialize the class with required parameters."""
        self.param1 = param1
        self.param2 = param2
        self._internal_state: list = []
    
    def public_method(self, value: str) -> bool:
        """
        Public method docstring.
        
        Args:
            value: Description of the parameter
            
        Returns:
            bool: Description of return value
        """
        self._internal_state.append(value)
        return True
    
    def _private_method(self) -> None:
        """Private method (convention, not enforced)."""
        pass
    
    @property
    def computed_property(self) -> int:
        """Property with computed value."""
        return len(self._internal_state)
    
    def __str__(self) -> str:
        """String representation for users."""
        return f"{self.__class__.__name__}(param1={self.param1})"
''',
            "async": '''import asyncio
import aiohttp
from typing import Optional


async def fetch_data(url: str, session: aiohttp.ClientSession) -> Optional[dict]:
    """Fetch data from URL asynchronously."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as e:
        print(f"Error fetching {url}: {e}")
        return None


async def main() -> None:
    """Main async entry point."""
    urls = [
        "https://api.example.com/data1",
        "https://api.example.com/data2",
    ]
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(url, session) for url in urls]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            if result:
                print(result)


if __name__ == "__main__":
    asyncio.run(main())
''',
            "test": '''import unittest
from typing import Optional


class TestFeature(unittest.TestCase):
    """Test cases for feature module."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        pass
    
    def tearDown(self) -> None:
        """Clean up after tests."""
        pass
    
    def test_example_success(self) -> None:
        """Test successful case."""
        result = True  # Replace with actual function call
        self.assertTrue(result)
    
    def test_example_failure(self) -> None:
        """Test failure case."""
        result = False  # Replace with actual function call
        self.assertFalse(result)
    
    def test_with_parameters(self) -> None:
        """Test with various input parameters."""
        test_cases = [
            (1, 2, 3),
            (0, 0, 0),
            (-1, 1, 0),
        ]
        
        for a, b, expected in test_cases:
            with self.subTest(a=a, b=b):
                result = a + b  # Replace with actual function
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
'''
        }
        
        return templates.get(template_type, f"Template '{template_type}' not found. Available: script, class, async, test")
    
    def explain_concept(self, concept: str) -> str:
        """Explain Python programming concepts."""
        concept_lower = concept.lower()
        
        explanations = {
            "decorator": """
Decorator in Python:
A decorator is a function that takes another function and extends its behavior without explicitly modifying it.

Syntax:
@my_decorator
def my_function():
    pass

Equivalent to:
def my_function():
    pass
my_function = my_decorator(my_function)

Example:
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Executed in {end-start:.4f}s")
        return result
    return wrapper

@timing_decorator
def slow_function():
    time.sleep(1)
""",
            "generator": """
Generator in Python:
A generator is a special type of iterator that generates values on-the-fly using 'yield'.

Benefits: Memory efficient, lazy evaluation

Example:
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# Usage:
for num in fibonacci(10):
    print(num)

# Generator expression:
squares = (x**2 for x in range(10))
""",
            "context_manager": """
Context Manager in Python:
Manages resources automatically using 'with' statement.

Implements __enter__ and __exit__ methods.

Example:
class FileManager:
    def __init__(self, filename):
        self.filename = filename
    
    def __enter__(self):
        self.file = open(self.filename, 'r')
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

# Usage:
with FileManager('data.txt') as f:
    content = f.read()

# Using contextlib:
from contextlib import contextmanager

@contextmanager
def managed_resource():
    resource = acquire()
    try:
        yield resource
    finally:
        release(resource)
""",
            "list_comprehension": """
List Comprehension in Python:
Concise way to create lists.

Syntax: [expression for item in iterable if condition]

Examples:
# Traditional:
squares = []
for x in range(10):
    squares.append(x**2)

# Comprehension:
squares = [x**2 for x in range(10)]

# With condition:
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# Nested:
matrix = [[i*j for j in range(3)] for i in range(3)]
""",
            "virtual_environment": """
Virtual Environment in Python:
Isolated Python environment for project-specific dependencies.

Creation:
python -m venv venv

Activation:
- Windows: venv\\Scripts\\activate
- macOS/Linux: source venv/bin/activate

Best Practices:
1. Create separate venv for each project
2. Add venv to .gitignore
3. Freeze dependencies: pip freeze > requirements.txt
4. Install: pip install -r requirements.txt

Alternative tools:
- poetry: Modern dependency management
- pipenv: Combines pip and virtualenv
- conda: Cross-language environment manager
"""
        }
        
        for key, explanation in explanations.items():
            if key in concept_lower:
                return explanation
        
        return f"Concept '{concept}' not found in knowledge base. Try: decorator, generator, context_manager, list_comprehension, virtual_environment"
    
    def run_safety_check(self, code: str) -> Dict[str, Any]:
        """Check code for potentially unsafe operations."""
        warnings = []
        
        # Check for eval/exec
        if re.search(r'\b(eval|exec)\s*\(', code):
            warnings.append({
                "severity": "HIGH",
                "issue": "Use of eval() or exec()",
                "recommendation": "Avoid eval/exec with untrusted input. Use ast.literal_eval() for safe parsing."
            })
        
        # Check for pickle with untrusted data
        if 'pickle.load' in code or 'pickle.loads' in code:
            warnings.append({
                "severity": "HIGH",
                "issue": "Use of pickle with potentially untrusted data",
                "recommendation": "Never unpickle data from untrusted sources. Use JSON instead."
            })
        
        # Check for shell injection risks
        if re.search(r'os\.system\s*\(|subprocess\.call\s*\([^[]', code):
            warnings.append({
                "severity": "MEDIUM",
                "issue": "Potential shell injection",
                "recommendation": "Use subprocess with list arguments and shell=False"
            })
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        for pattern in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                warnings.append({
                    "severity": "HIGH",
                    "issue": "Hardcoded secret detected",
                    "recommendation": "Use environment variables or secure secret management"
                })
                break
        
        # Check for SQL injection risks
        if re.search(r'execute\s*\(\s*f["\']|execute\s*\([^"]*%|execute\s*\([^"]*\+', code):
            warnings.append({
                "severity": "HIGH",
                "issue": "Potential SQL injection",
                "recommendation": "Use parameterized queries instead of string formatting"
            })
        
        return {
            "status": "checked",
            "warnings": warnings,
            "safe": len(warnings) == 0,
            "recommendation": "Code appears safe" if len(warnings) == 0 else f"Found {len(warnings)} security concern(s)"
        }
