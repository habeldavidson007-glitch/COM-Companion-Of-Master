"""
Godot Scene Parser - Parses .tscn and .tres files to extract node structure.

Godot scene files are text-based INI-like format. This parser extracts:
- Node names and types
- Parent-child relationships  
- Node paths in the scene tree
- Resource references

Supports Godot 4.x format (text-based .tscn)
"""

import re
from typing import Dict, List, Optional, Any, Set
from pathlib import Path


class SceneNode:
    """Represents a single node in a Godot scene."""
    
    def __init__(self, name: str, node_type: str, parent_path: str):
        self.name = name
        self.type = node_type
        self.parent_path = parent_path
        self.path = f"{parent_path}/{name}" if parent_path != "." else name
        self.children: List[str] = []
        self.properties: Dict[str, Any] = {}
    
    def __repr__(self):
        return f"SceneNode({self.path!r}, type={self.type!r})"


class SceneParser:
    """Parses Godot .tscn scene files into structured data."""
    
    # Regex patterns for Godot 4.x scene format
    NODE_PATTERN = re.compile(
        r'^\[(node|subnode)\s+'
        r'name="([^"]+)"\s+'
        r'(?:type="([^"]+)"\s+)?'
        r'(?:parent="([^"]*)")?'
        r'(?:instance=.*?\s+)?'
        r'\]',
        re.MULTILINE
    )
    
    SUBRESOURCE_PATTERN = re.compile(
        r'^\[sub_resource\s+type="([^"]+)"\s+id="([^"]+)"\]',
        re.MULTILINE
    )
    
    PROPERTY_PATTERN = re.compile(
        r'^(\w+)\s*=\s*(.+)$',
        re.MULTILINE
    )
    
    def __init__(self):
        self.scenes: Dict[str, Dict[str, SceneNode]] = {}  # file_path -> {node_path: SceneNode}
    
    def parse_file(self, file_path: str) -> Dict[str, SceneNode]:
        """
        Parse a .tscn or .tres file and return a dict of node_path -> SceneNode.
        
        Args:
            file_path: Path to the .tscn or .tres file
            
        Returns:
            Dictionary mapping node paths to SceneNode objects
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Scene file not found: {file_path}")
        
        content = path.read_text(encoding='utf-8')
        nodes = self._parse_content(content, str(path))
        self.scenes[str(path)] = nodes
        return nodes
    
    def _parse_content(self, content: str, file_path: str) -> Dict[str, SceneNode]:
        """Parse scene file content into nodes."""
        nodes: Dict[str, SceneNode] = {}
        
        # Track current section for property parsing
        current_node_path: Optional[str] = None
        
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith(';'):
                i += 1
                continue
            
            # Check for node definition
            node_match = self.NODE_PATTERN.match(line)
            if node_match:
                node_type_kw, name, node_type, parent = node_match.groups()
                
                # Default type based on keyword
                if not node_type:
                    node_type = "Node" if node_type_kw == "node" else "Node"
                
                # Default parent is root
                if not parent:
                    parent = "."
                
                # Create node
                node = SceneNode(name, node_type, parent)
                nodes[node.path] = node
                
                # Register as child of parent
                if parent in nodes:
                    nodes[parent].children.append(node.path)
                
                current_node_path = node.path
                i += 1
                continue
            
            # Check for sub-resource (external scene reference)
            subres_match = self.SUBRESOURCE_PATTERN.match(line)
            if subres_match:
                # Sub-resources are tracked but not expanded here
                i += 1
                continue
            
            # Parse properties if we're in a node section
            if current_node_path and current_node_path in nodes:
                prop_match = self.PROPERTY_PATTERN.match(line)
                if prop_match:
                    prop_name, prop_value = prop_match.groups()
                    nodes[current_node_path].properties[prop_name] = self._parse_value(prop_value)
            
            i += 1
        
        return nodes
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a Godot property value string into Python type."""
        value_str = value_str.strip()
        
        # Remove quotes from strings
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        
        # Boolean
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # Null
        if value_str.lower() == 'null':
            return None
        
        # Number (int or float)
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        
        # Vector2, Vector3, Color, etc. - keep as string for now
        return value_str
    
    def get_all_node_paths(self, file_path: str) -> Set[str]:
        """Get all node paths in a scene."""
        if str(file_path) not in self.scenes:
            self.parse_file(file_path)
        return set(self.scenes[str(file_path)].keys())
    
    def get_node(self, file_path: str, node_path: str) -> Optional[SceneNode]:
        """Get a specific node by path."""
        if str(file_path) not in self.scenes:
            self.parse_file(file_path)
        return self.scenes[str(file_path)].get(node_path)
    
    def validate_node_exists(self, file_path: str, node_path: str) -> bool:
        """Check if a node path exists in the scene."""
        if str(file_path) not in self.scenes:
            self.parse_file(file_path)
        
        # Handle relative paths (starting with $)
        if node_path.startswith('$'):
            node_path = node_path[1:]  # Remove leading $
        
        # Normalize path separators
        node_path = node_path.replace('\\', '/')
        
        return node_path in self.scenes[str(file_path)]
    
    def suggest_similar_path(self, file_path: str, invalid_path: str) -> Optional[str]:
        """
        Suggest a similar node path if the given one doesn't exist.
        Uses simple string similarity matching.
        """
        if str(file_path) not in self.scenes:
            self.parse_file(file_path)
        
        invalid_name = invalid_path.rstrip('/').split('/')[-1]
        candidates = list(self.scenes[str(file_path)].keys())
        
        # Extract just the node name from each candidate
        candidate_names = {c: c.rstrip('/').split('/')[-1] for c in candidates}
        
        # Find best match using simple heuristic
        best_match = None
        best_score = 0
        
        for full_path, name in candidate_names.items():
            # Score based on common prefix length
            score = 0
            min_len = min(len(invalid_name), len(name))
            for i in range(min_len):
                if invalid_name[i] == name[i]:
                    score += 1
                else:
                    break
            
            # Bonus if one contains the other
            if invalid_name in name or name in invalid_name:
                score += 5
            
            if score > best_score and score >= 3:  # Minimum threshold
                best_score = score
                best_match = full_path
        
        return best_match
