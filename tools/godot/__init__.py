"""
COM Godot Module - Phase 1: Project Scanner + Error Explainer
Specialized tools for Godot project parsing and analysis.

This module provides:
- Scene tree parsing from .tscn files
- Script parsing for @onready vars, $NodePath refs, signals
- Project-wide node path validation
- Real-time log watching for error explanation
"""

from .scene_parser import SceneParser
from .script_parser import ScriptParser  
from .project_map import ProjectMap, ValidationError
from .log_watcher import LogWatcher

__all__ = [
    'SceneParser',
    'ScriptParser',
    'ProjectMap', 
    'ValidationError',
    'LogWatcher'
]
