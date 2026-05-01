"""
GDScript Parser - Extracts node references, signals, and variables from .gd files.

Parses GDScript to find:
- @onready variable declarations with $NodePath references
- Direct $NodePath usage in code
- Signal connections (connect(), signal keywords)
- Class structure and function definitions

This enables pre-runtime validation of node bindings.
"""

import re
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class NodeReference:
    """Represents a $NodePath reference found in a script."""
    file_path: str
    line_number: int
    node_path: str
    context: str  # The full line or expression
    var_name: Optional[str] = None  # If part of @onready declaration


@dataclass  
class SignalConnection:
    """Represents a signal connection found in a script."""
    file_path: str
    line_number: int
    signal_name: str
    target_node: Optional[str]  # e.g., "player" from $Player
    target_method: str  # e.g., "take_damage"
    connection_type: str  # 'connect' keyword or 'signal' declaration


@dataclass
class OnReadyVar:
    """Represents an @onready variable declaration."""
    file_path: str
    line_number: int
    var_name: str
    node_path: str
    node_type: Optional[str] = None  # If type annotation exists


class ScriptParser:
    """Parses GDScript files to extract node references and signal connections."""
    
    # Pattern for @onready var declarations with $NodePath
    ONREADY_PATTERN = re.compile(
        r'^\s*@onready\s+var\s+(\w+)\s*(?::\s*[^=]+)?\s*=\s*(\$[^\s\(]+)',
        re.MULTILINE
    )
    
    # Pattern for direct $NodePath usage (not in strings)
    NODEPATH_PATTERN = re.compile(
        r'\$([A-Za-z_][A-Za-z0-9_/]*)',
        re.MULTILINE
    )
    
    # Pattern for signal connections: .connect("signal_name", callable)
    CONNECT_PATTERN = re.compile(
        r'(\$?[A-Za-z_][A-Za-z0-9_]*)\.connect\s*\(\s*["\']([^"\']+)["\']\s*,\s*(?:&?["\']?([A-Za-z_][A-Za-z0-9_]*)["\']?|self\.([A-Za-z_][A-Za-z0-9_]*))',
        re.MULTILINE
    )
    
    # Pattern for signal declarations
    SIGNAL_DECL_PATTERN = re.compile(
        r'^\s*signal\s+(\w+)',
        re.MULTILINE
    )
    
    def __init__(self):
        self.scripts: Dict[str, Dict[str, Any]] = {}  # file_path -> parsed data
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a .gd file and extract all relevant information.
        
        Returns dict with keys:
        - onready_vars: List[OnReadyVar]
        - node_refs: List[NodeReference]
        - signal_connections: List[SignalConnection]
        - signals: List[str] (declared signals)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Script file not found: {file_path}")
        
        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        result = {
            'onready_vars': [],
            'node_refs': [],
            'signal_connections': [],
            'signals': []
        }
        
        # Find @onready declarations
        for match in self.ONREADY_PATTERN.finditer(content):
            var_name = match.group(1)
            node_path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            
            result['onready_vars'].append(OnReadyVar(
                file_path=str(path),
                line_number=line_num,
                var_name=var_name,
                node_path=node_path
            ))
            
            # Also add as node reference
            result['node_refs'].append(NodeReference(
                file_path=str(path),
                line_number=line_num,
                node_path=node_path,
                context=lines[line_num - 1].strip() if line_num <= len(lines) else "",
                var_name=var_name
            ))
        
        # Find all $NodePath references (excluding those already captured)
        onready_paths = {v.node_path for v in result['onready_vars']}
        for match in self.NODEPATH_PATTERN.finditer(content):
            node_path = '$' + match.group(1)
            if node_path in onready_paths:
                continue  # Already captured
            
            # Calculate line number
            line_num = content[:match.start()].count('\n') + 1
            
            # Skip if inside a string (simple heuristic)
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            if f'"{node_path}"' in line_content or f"'{node_path}'" in line_content:
                continue
            
            result['node_refs'].append(NodeReference(
                file_path=str(path),
                line_number=line_num,
                node_path=node_path,
                context=line_content.strip()
            ))
        
        # Find signal connections
        for match in self.CONNECT_PATTERN.finditer(content):
            source_node = match.group(1)
            signal_name = match.group(2)
            target_method = match.group(3) or match.group(4)
            line_num = content[:match.start()].count('\n') + 1
            
            result['signal_connections'].append(SignalConnection(
                file_path=str(path),
                line_number=line_num,
                signal_name=signal_name,
                target_node=source_node if source_node.startswith('$') else None,
                target_method=target_method,
                connection_type='connect'
            ))
        
        # Find signal declarations
        for match in self.SIGNAL_DECL_PATTERN.finditer(content):
            signal_name = match.group(1)
            result['signals'].append(signal_name)
        
        self.scripts[str(path)] = result
        return result
    
    def get_all_node_paths(self, file_path: str) -> Set[str]:
        """Get all $NodePath references from a script."""
        if str(file_path) not in self.scripts:
            self.parse_file(file_path)
        
        paths = set()
        for ref in self.scripts[str(file_path)]['node_refs']:
            paths.add(ref.node_path)
        return paths
    
    def get_onready_vars(self, file_path: str) -> List[OnReadyVar]:
        """Get all @onready variable declarations."""
        if str(file_path) not in self.scripts:
            self.parse_file(file_path)
        return self.scripts[str(file_path)]['onready_vars']
    
    def get_signal_connections(self, file_path: str) -> List[SignalConnection]:
        """Get all signal connections."""
        if str(file_path) not in self.scripts:
            self.parse_file(file_path)
        return self.scripts[str(file_path)]['signal_connections']
    
    def validate_node_path(self, file_path: str, node_path: str, 
                          scene_file: str, scene_nodes: Set[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a node path exists in the target scene.
        
        Args:
            file_path: The script file containing the reference
            node_path: The $NodePath to validate (e.g., "$Player")
            scene_file: The scene file to check against
            scene_nodes: Set of valid node paths in the scene
            
        Returns:
            Tuple of (is_valid, suggestion_if_invalid)
        """
        # Remove leading $ if present
        clean_path = node_path.lstrip('$')
        
        # Handle relative paths starting with ../
        if clean_path.startswith('../'):
            # Relative parent navigation - complex, skip for now
            return True, None
        
        # Check if path exists
        if clean_path in scene_nodes:
            return True, None
        
        # Try without trailing slashes
        clean_path = clean_path.rstrip('/')
        if clean_path in scene_nodes:
            return True, None
        
        # Path doesn't exist - try to suggest alternative
        suggestion = self._suggest_similar_node(clean_path, scene_nodes)
        return False, suggestion
    
    def _suggest_similar_node(self, invalid_path: str, valid_nodes: Set[str]) -> Optional[str]:
        """Suggest a similar node path using simple string matching."""
        invalid_name = invalid_path.split('/')[-1]
        
        best_match = None
        best_score = 0
        
        for valid_path in valid_nodes:
            valid_name = valid_path.split('/')[-1]
            
            # Score based on common prefix
            score = 0
            min_len = min(len(invalid_name), len(valid_name))
            for i in range(min_len):
                if invalid_name[i] == valid_name[i]:
                    score += 1
                else:
                    break
            
            # Bonus for containment
            if invalid_name in valid_name or valid_name in invalid_name:
                score += 5
            
            if score > best_score and score >= 3:
                best_score = score
                best_match = valid_path
        
        return best_match
