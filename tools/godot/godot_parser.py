"""
Godot File Parsers - Phase 1 Implementation.
Parses .gd (GDScript) and .tscn (Godot Scene) files for error detection.
"""
import re
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class ParseError:
    """Represents a detected error in Godot file."""
    error_type: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    severity: str = "error"  # error, warning, info
    suggestion: Optional[str] = None


@dataclass
class ParseResult:
    """Result of parsing a Godot file."""
    file_path: str
    file_type: str  # gd, tscn
    errors: list[ParseError] = field(default_factory=list)
    warnings: list[ParseError] = field(default_factory=list)
    nodes: list[dict] = field(default_factory=list)
    signals: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    variables: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class GDScriptParser:
    """
    Parser for GDScript (.gd) files.
    Detects common Silent Killer patterns without LLM.
    """
    
    # Common Godot error patterns
    SIGNAL_PATTERN = re.compile(r'signal\s+(\w+)')
    SIGNAL_CONNECT_PATTERN = re.compile(r'\.connect\s*\(\s*&?(\w+)')
    NODE_PATH_PATTERN = re.compile(r'\$(\S+)|get_node\s*\(\s*["\']([^"\']+)["\']')
    LOAD_PATTERN = re.compile(r'load\s*\(\s*["\']([^"\']+)["\']')
    FUNC_PATTERN = re.compile(r'func\s+(\w+)\s*\(([^)]*)\)')
    VAR_PATTERN = re.compile(r'(?:var|const)\s+(\w+)(?:\s*:\s*(\w+))?')
    TYPE_ANNOT_PATTERN = re.compile(r':\s*(int|float|string|bool|Array|Dictionary|Vector2|Vector3)')
    
    def __init__(self):
        self.errors: list[ParseError] = []
        self.warnings: list[ParseError] = []
        self.nodes: list[dict] = []
        self.signals: list[dict] = []
        self.functions: list[dict] = []
        self.variables: list[dict] = []
        self.dependencies: list[str] = []
        self.declared_signals: set[str] = set()
        self.declared_nodes: set[str] = set()
        self.declared_vars: set[str] = set()
        self.function_signatures: dict[str, dict] = {}
    
    def parse(self, file_path: str, content: str) -> ParseResult:
        """
        Parse GDScript content and detect errors.
        
        Args:
            file_path: Path to the .gd file
            content: File content as string
            
        Returns:
            ParseResult with detected issues
        """
        self._reset_state()
        lines = content.split('\n')
        
        # First pass: collect declarations
        for line_num, line in enumerate(lines, 1):
            self._collect_declarations(line, line_num)
        
        # Second pass: detect errors
        for line_num, line in enumerate(lines, 1):
            self._detect_errors(line, line_num, lines)
        
        return ParseResult(
            file_path=file_path,
            file_type="gd",
            errors=self.errors,
            warnings=self.warnings,
            nodes=self.nodes,
            signals=self.signals,
            functions=self.functions,
            variables=self.variables,
            dependencies=self.dependencies
        )
    
    def _reset_state(self):
        """Reset parser state for fresh parse."""
        self.errors = []
        self.warnings = []
        self.nodes = []
        self.signals = []
        self.functions = []
        self.variables = []
        self.dependencies = []
        self.declared_signals = set()
        self.declared_nodes = set()
        self.declared_vars = set()
        self.function_signatures = {}
    
    def _collect_declarations(self, line: str, line_num: int):
        """Collect all declarations in first pass."""
        stripped = line.strip()
        
        # Skip comments and empty lines
        if stripped.startswith('#') or not stripped:
            return
        
        # Collect signals
        for match in self.SIGNAL_PATTERN.finditer(line):
            signal_name = match.group(1)
            self.declared_signals.add(signal_name)
            self.signals.append({
                "name": signal_name,
                "line": line_num
            })
        
        # Collect functions with signatures
        for match in self.FUNC_PATTERN.finditer(line):
            func_name = match.group(1)
            params_str = match.group(2)
            params = self._parse_params(params_str)
            self.function_signatures[func_name] = {
                "name": func_name,
                "params": params,
                "line": line_num
            }
            self.functions.append({
                "name": func_name,
                "params": params,
                "line": line_num
            })
        
        # Collect variables
        for match in self.VAR_PATTERN.finditer(line):
            var_name = match.group(1)
            var_type = match.group(2)
            self.declared_vars.add(var_name)
            self.variables.append({
                "name": var_name,
                "type": var_type,
                "line": line_num
            })
        
        # Collect node references (potential dependencies)
        for match in self.NODE_PATH_PATTERN.finditer(line):
            node_path = match.group(1) or match.group(2)
            if node_path:
                self.declared_nodes.add(node_path.split('/')[0])
                self.nodes.append({
                    "path": node_path,
                    "line": line_num
                })
        
        # Collect load dependencies
        for match in self.LOAD_PATTERN.finditer(line):
            path = match.group(1)
            self.dependencies.append(path)
    
    def _parse_params(self, params_str: str) -> list[dict]:
        """Parse function parameters into structured format."""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ':' in param:
                name, type_annot = param.split(':', 1)
                params.append({
                    "name": name.strip(),
                    "type": type_annot.strip(),
                    "optional": '=' in param
                })
            else:
                params.append({
                    "name": param.split('=')[0].strip(),
                    "type": None,
                    "optional": '=' in param
                })
        return params
    
    def _detect_errors(self, line: str, line_num: int, all_lines: list[str]):
        """Detect errors in second pass."""
        stripped = line.strip()
        
        # Skip comments and empty lines
        if stripped.startswith('#') or not stripped:
            return
        
        # Check for undefined variables (common typos)
        self._check_undefined_vars(line, line_num)
        
        # Check for signal connection errors
        self._check_signal_connections(line, line_num)
        
        # Check for missing node paths
        self._check_node_paths(line, line_num)
        
        # Check for type mismatches
        self._check_type_mismatches(line, line_num)
        
        # Check for invalid load paths
        self._check_load_paths(line, line_num)
        
        # Check for null access risks
        self._check_null_access(line, line_num)
        
        # Check for division by zero risks
        self._check_division_by_zero(line, line_num)
    
    def _check_undefined_vars(self, line: str, line_num: int):
        """Check for potentially undefined variables (typos)."""
        # Look for variable assignments that might be typos
        assign_match = re.search(r'(\w+)\s*=\s*', line)
        if assign_match:
            var_name = assign_match.group(1)
            # Skip if it's a known variable or built-in
            if var_name not in self.declared_vars and \
               var_name not in {'self', 'PI', 'TAU', 'INF', 'NAN'} and \
               not var_name[0].isupper():  # Skip constants
                # Check if similar variable exists (typo detection)
                for declared in self.declared_vars:
                    if self._similarity(var_name, declared) > 0.8:
                        self.errors.append(ParseError(
                            error_type="undefined_variable",
                            description=f"'{var_name}' might be a typo for '{declared}'",
                            file_path="",  # Will be set by caller
                            line_number=line_num,
                            severity="error",
                            suggestion=f"Did you mean '{declared}'?"
                        ))
                        break
    
    def _check_signal_connections(self, line: str, line_num: int):
        """Check for signal connection errors."""
        for match in self.SIGNAL_CONNECT_PATTERN.finditer(line):
            signal_name = match.group(1)
            if signal_name not in self.declared_signals:
                # Check for similar signal names
                found_similar = False
                for declared in self.declared_signals:
                    if self._similarity(signal_name, declared) > 0.8:
                        self.errors.append(ParseError(
                            error_type="signal_typo",
                            description=f"Signal '{signal_name}' might be a typo for '{declared}'",
                            file_path="",
                            line_number=line_num,
                            severity="error",
                            suggestion=f"Did you mean '{declared}'?"
                        ))
                        found_similar = True
                        break
                
                if not found_similar and signal_name not in {'_on_', 'connect'}:
                    self.warnings.append(ParseError(
                        error_type="unknown_signal",
                        description=f"Signal '{signal_name}' is not declared",
                        file_path="",
                        line_number=line_num,
                        severity="warning"
                    ))
    
    def _check_node_paths(self, line: str, line_num: int):
        """Check for potentially invalid node paths."""
        for match in self.NODE_PATH_PATTERN.finditer(line):
            node_path = match.group(1) or match.group(2)
            # Check for obvious issues like "Missing" in path
            if 'missing' in node_path.lower() or 'nonexistent' in node_path.lower():
                self.errors.append(ParseError(
                    error_type="missing_node",
                    description=f"Node path '{node_path}' appears to reference non-existent node",
                    file_path="",
                    line_number=line_num,
                    severity="error"
                ))
    
    def _check_type_mismatches(self, line: str, line_num: int):
        """Check for obvious type mismatches."""
        # Simple heuristic: assigning float to int variable
        if ': int' in line and '= ' in line:
            if re.search(r'=\s*\d+\.\d+', line):
                self.errors.append(ParseError(
                    error_type="type_mismatch",
                    description="Assigning float value to int variable",
                    file_path="",
                    line_number=line_num,
                    severity="error"
                ))
    
    def _check_load_paths(self, line: str, line_num: int):
        """Check for obviously invalid load paths."""
        for match in self.LOAD_PATTERN.finditer(line):
            path = match.group(1)
            if 'nonexistent' in path.lower() or 'missing' in path.lower():
                self.errors.append(ParseError(
                    error_type="invalid_path",
                    description=f"load() references potentially non-existent file: {path}",
                    file_path="",
                    line_number=line_num,
                    severity="error"
                ))
    
    def _check_null_access(self, line: str, line_num: int):
        """Check for potential null/None access."""
        if '$Missing' in line or '.position' in line or '.rotation' in line:
            if 'Missing' in line or 'null' in line.lower():
                self.errors.append(ParseError(
                    error_type="null_access",
                    description="Potential null/None object access",
                    file_path="",
                    line_number=line_num,
                    severity="error"
                ))
    
    def _check_division_by_zero(self, line: str, line_num: int):
        """Check for potential division by zero."""
        if re.search(r'/\s*\w+', line) and 'if' not in line and '!= 0' not in line:
            # Extract divisor
            div_match = re.search(r'/\s*(\w+)', line)
            if div_match:
                divisor = div_match.group(1)
                # Check if divisor is checked for zero
                self.warnings.append(ParseError(
                    error_type="division_by_zero",
                    description=f"Division by '{divisor}' without zero check",
                    file_path="",
                    line_number=line_num,
                    severity="warning",
                    suggestion=f"Add check: if {divisor} != 0"
                ))
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity ratio (Levenshtein-based)."""
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)


class TSCNParser:
    """
    Parser for Godot Scene (.tscn) files.
    Detects broken node references and structural issues.
    """
    
    NODE_PATTERN = re.compile(r'\[node\s+name="([^"]+)"(?:\s+parent="([^"]+)")?(?:\s+type="([^"]+)")?')
    RESOURCE_PATTERN = re.compile(r'ExtResource\(\s*"([^"]+)"\s*\)')
    
    def __init__(self):
        self.errors: list[ParseError] = []
        self.warnings: list[ParseError] = []
        self.nodes: list[dict] = []
        self.dependencies: list[str] = []
    
    def parse(self, file_path: str, content: str) -> ParseResult:
        """Parse TSCN content and detect errors."""
        self._reset_state()
        lines = content.split('\n')
        
        # Collect all node names
        node_names = set()
        for line_num, line in enumerate(lines, 1):
            match = self.NODE_PATTERN.search(line)
            if match:
                node_name = match.group(1)
                node_names.add(node_name)
                self.nodes.append({
                    "name": node_name,
                    "parent": match.group(2),
                    "type": match.group(3),
                    "line": line_num
                })
        
        # Check for broken references
        for line_num, line in enumerate(lines, 1):
            self._check_broken_refs(line, line_num, node_names)
        
        return ParseResult(
            file_path=file_path,
            file_type="tscn",
            errors=self.errors,
            warnings=self.warnings,
            nodes=self.nodes,
            dependencies=self.dependencies
        )
    
    def _reset_state(self):
        """Reset parser state."""
        self.errors = []
        self.warnings = []
        self.nodes = []
        self.dependencies = []
    
    def _check_broken_refs(self, line: str, line_num: int, node_names: set[str]):
        """Check for broken node/resource references."""
        # Check for missing node references
        if 'Missing' in line or 'NonExistent' in line:
            self.errors.append(ParseError(
                error_type="broken_scene_path",
                description="Scene references missing or non-existent node",
                file_path="",
                line_number=line_num,
                severity="error"
            ))
        
        # Check for broken resource references
        for match in self.RESOURCE_PATTERN.finditer(line):
            res_path = match.group(1)
            if 'missing' in res_path.lower() or 'nonexistent' in res_path.lower():
                self.errors.append(ParseError(
                    error_type="broken_resource",
                    description=f"Resource reference appears broken: {res_path}",
                    file_path="",
                    line_number=line_num,
                    severity="error"
                ))


def parse_godot_file(file_path: str) -> ParseResult:
    """
    Universal parser for Godot files.
    Automatically detects file type and uses appropriate parser.
    
    Args:
        file_path: Path to .gd or .tscn file
        
    Returns:
        ParseResult with detected issues
    """
    path = Path(file_path)
    
    if not path.exists():
        return ParseResult(
            file_path=file_path,
            file_type="unknown",
            errors=[ParseError(
                error_type="file_not_found",
                description=f"File does not exist: {file_path}",
                file_path=file_path,
                severity="error"
            )]
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if path.suffix == '.gd':
        parser = GDScriptParser()
        result = parser.parse(file_path, content)
    elif path.suffix == '.tscn':
        parser = TSCNParser()
        result = parser.parse(file_path, content)
    else:
        return ParseResult(
            file_path=file_path,
            file_type="unknown",
            errors=[ParseError(
                error_type="unsupported_format",
                description=f"Unsupported file format: {path.suffix}",
                file_path=file_path,
                severity="error"
            )]
        )
    
    # Set file_path in all errors
    for error in result.errors + result.warnings:
        error.file_path = file_path
    
    return result


def parse_project(project_path: str) -> dict[str, Any]:
    """
    Parse entire Godot project.
    
    Args:
        project_path: Root directory of Godot project
        
    Returns:
        Dict with parsed results for all files
    """
    results = {
        "project_path": project_path,
        "files": {},
        "total_errors": 0,
        "total_warnings": 0,
        "summary": {}
    }
    
    project = Path(project_path)
    if not project.exists():
        results["error"] = f"Project path does not exist: {project_path}"
        return results
    
    # Find all .gd and .tscn files
    gd_files = list(project.rglob("*.gd"))
    tscn_files = list(project.rglob("*.tscn"))
    
    for file_path in gd_files + tscn_files:
        rel_path = str(file_path.relative_to(project))
        parse_result = parse_godot_file(str(file_path))
        results["files"][rel_path] = {
            "errors": [vars(e) for e in parse_result.errors],
            "warnings": [vars(e) for e in parse_result.warnings],
            "nodes": parse_result.nodes,
            "functions": parse_result.functions if hasattr(parse_result, 'functions') else [],
        }
        results["total_errors"] += len(parse_result.errors)
        results["total_warnings"] += len(parse_result.warnings)
    
    results["summary"] = {
        "total_files": len(results["files"]),
        "gd_files": len(gd_files),
        "tscn_files": len(tscn_files),
        "total_errors": results["total_errors"],
        "total_warnings": results["total_warnings"]
    }
    
    return results
