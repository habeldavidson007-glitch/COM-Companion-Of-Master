"""
Project Map - Combines scene tree and script analysis for project-wide validation.

This is the core data structure that represents the entire Godot project:
- All scenes and their node structures
- All scripts and their node references
- Cross-referenced validation of node paths
- Error reporting with suggestions
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from .scene_parser import SceneParser, SceneNode
from .script_parser import ScriptParser, NodeReference, OnReadyVar


@dataclass
class ValidationError:
    """Represents a validation error found in the project."""
    error_type: str  # 'missing_node', 'invalid_signal', 'orphaned_reference'
    file_path: str
    line_number: int
    message: str
    suggestion: Optional[str] = None
    severity: str = 'error'  # 'error', 'warning', 'info'
    
    def __str__(self):
        base = f"[{self.severity.upper()}] {self.file_path}:{self.line_number} - {self.message}"
        if self.suggestion:
            base += f"\n  → Did you mean: {self.suggestion}?"
        return base


@dataclass
class SceneInfo:
    """Metadata about a parsed scene."""
    file_path: str
    nodes: Dict[str, SceneNode]
    root_type: str
    node_count: int


@dataclass  
class ScriptInfo:
    """Metadata about a parsed script."""
    file_path: str
    onready_vars: List[OnReadyVar]
    node_refs: List[NodeReference]
    attached_scene: Optional[str] = None  # If script is attached to a scene


class ProjectMap:
    """
    Represents the entire Godot project structure.
    
    Combines scene parsing and script parsing to enable:
    - Pre-runtime node path validation
    - Signal connection verification
    - Project health analysis
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.scene_parser = SceneParser()
        self.script_parser = ScriptParser()
        
        self.scenes: Dict[str, SceneInfo] = {}  # scene_file -> SceneInfo
        self.scripts: Dict[str, ScriptInfo] = {}  # script_file -> ScriptInfo
        self.errors: List[ValidationError] = []
        self._scanned = False
    
    def scan_project(self) -> None:
        """
        Scan the entire project directory for scenes and scripts.
        Populates self.scenes and self.scripts.
        """
        if self._scanned:
            return
        
        # Find all .tscn files
        for tscn_file in self.project_root.rglob("*.tscn"):
            try:
                nodes = self.scene_parser.parse_file(str(tscn_file))
                if nodes:
                    root_node = nodes.get('.', list(nodes.values())[0] if nodes else None)
                    self.scenes[str(tscn_file)] = SceneInfo(
                        file_path=str(tscn_file),
                        nodes=nodes,
                        root_type=root_node.type if root_node else "Unknown",
                        node_count=len(nodes)
                    )
            except Exception as e:
                print(f"Warning: Failed to parse {tscn_file}: {e}")
        
        # Find all .gd files
        for gd_file in self.project_root.rglob("*.gd"):
            try:
                data = self.script_parser.parse_file(str(gd_file))
                self.scripts[str(gd_file)] = ScriptInfo(
                    file_path=str(gd_file),
                    onready_vars=data['onready_vars'],
                    node_refs=data['node_refs']
                )
            except Exception as e:
                print(f"Warning: Failed to parse {gd_file}: {e}")
        
        self._scanned = True
    
    def validate_node_paths(self) -> List[ValidationError]:
        """
        Validate all $NodePath references against actual scene trees.
        
        Returns list of ValidationErrors for any invalid paths.
        """
        if not self._scanned:
            self.scan_project()
        
        errors = []
        
        # Check each script's node references
        for script_path, script_info in self.scripts.items():
            # Try to find the associated scene
            # Heuristic: script at res://player/player.gd -> scene at res://player/player.tscn
            script_dir = Path(script_path).parent
            script_name = Path(script_path).stem
            potential_scene = script_dir / f"{script_name}.tscn"
            
            scene_to_check = None
            if str(potential_scene) in self.scenes:
                scene_to_check = self.scenes[str(potential_scene)]
            elif self.scenes:
                # Fallback: check against first scene (often main scene)
                scene_to_check = list(self.scenes.values())[0]
            
            if not scene_to_check:
                continue
            
            scene_nodes = set(scene_to_check.nodes.keys())
            
            # Validate each node reference
            for ref in script_info.node_refs:
                is_valid, suggestion = self.script_parser.validate_node_path(
                    ref.file_path,
                    ref.node_path,
                    scene_to_check.file_path,
                    scene_nodes
                )
                
                if not is_valid:
                    errors.append(ValidationError(
                        error_type='missing_node',
                        file_path=ref.file_path,
                        line_number=ref.line_number,
                        message=f"Node path '{ref.node_path}' not found in {Path(scene_to_check.file_path).name}",
                        suggestion=f"${suggestion}" if suggestion else None,
                        severity='error'
                    ))
        
        self.errors = errors
        return errors
    
    def get_node_suggestions(self, scene_file: str, partial_path: str) -> List[str]:
        """
        Get suggested node paths for a partial input.
        
        Useful for autocomplete or typo correction.
        """
        if str(scene_file) not in self.scenes:
            return []
        
        scene = self.scenes[str(scene_file)]
        partial = partial_path.lstrip('$').lower()
        
        suggestions = []
        for node_path in scene.nodes.keys():
            if partial in node_path.lower():
                suggestions.append(node_path)
        
        return suggestions[:10]  # Limit to top 10
    
    def get_project_stats(self) -> Dict[str, int]:
        """Get basic statistics about the project."""
        if not self._scanned:
            self.scan_project()
        
        total_nodes = sum(s.node_count for s in self.scenes.values())
        total_scripts = len(self.scripts)
        total_refs = sum(len(s.node_refs) for s in self.scripts.values())
        
        return {
            'scenes': len(self.scenes),
            'scripts': total_scripts,
            'total_nodes': total_nodes,
            'node_references': total_refs,
            'validation_errors': len(self.errors)
        }
    
    def refresh_file(self, file_path: str) -> None:
        """
        Re-parse a single file that has changed.
        
        Call this when a file is saved to update the project map.
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / file_path
        
        if path.suffix == '.tscn':
            try:
                nodes = self.scene_parser.parse_file(str(path))
                if nodes:
                    root_node = list(nodes.values())[0]
                    self.scenes[str(path)] = SceneInfo(
                        file_path=str(path),
                        nodes=nodes,
                        root_type=root_node.type,
                        node_count=len(nodes)
                    )
            except Exception:
                pass
        
        elif path.suffix == '.gd':
            try:
                data = self.script_parser.parse_file(str(path))
                self.scripts[str(path)] = ScriptInfo(
                    file_path=str(path),
                    onready_vars=data['onready_vars'],
                    node_refs=data['node_refs']
                )
            except Exception:
                pass
        
        # Re-validate after refresh
        self.validate_node_paths()
    
    def export_tree(self, scene_file: str) -> str:
        """
        Export the scene tree as a text representation.
        
        Useful for debugging or display in UI.
        """
        if str(scene_file) not in self.scenes:
            return f"Scene not found: {scene_file}"
        
        scene = self.scenes[str(scene_file)]
        lines = [f"Scene: {Path(scene_file).name}"]
        lines.append("=" * 40)
        
        # Build tree structure
        def build_tree(node_path: str, indent: int = 0) -> List[str]:
            result = []
            node = scene.nodes.get(node_path)
            if not node:
                return result
            
            prefix = "  " * indent
            result.append(f"{prefix}{node.name} ({node.type})")
            
            for child_path in node.children:
                result.extend(build_tree(child_path, indent + 1))
            
            return result
        
        # Start from root
        if '.' in scene.nodes:
            lines.extend(build_tree('.'))
        else:
            # No explicit root, list all nodes
            for node_path in sorted(scene.nodes.keys()):
                lines.extend(build_tree(node_path))
        
        return '\n'.join(lines)
