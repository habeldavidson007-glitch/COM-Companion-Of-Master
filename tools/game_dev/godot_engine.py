"""
Godot Engine Module for COM
Specialized in GDScript 4.x, node hierarchy, signals, and Godot project structure.
"""

import os
import re
from typing import Dict, List, Any, Optional
from tools.base import BaseTool

class GodotEngineTool(BaseTool):
    """Tool for Godot Game Development assistance."""
    
    def __init__(self):
        super().__init__()
        self.name = "GodotEngineTool"
        self.description = "Expert in Godot 4.x engine, GDScript, scene management, signals, and game architecture patterns."
        self.gdscript_keywords = [
            "extends", "class_name", "signal", "enum", "const", "var", "static",
            "func", "return", "if", "elif", "else", "for", "while", "match",
            "break", "continue", "pass", "await", "yield", "super", "self"
        ]
        self.node_types = [
            "Node", "Node2D", "Node3D", "Control", "CanvasLayer", "Sprite2D",
            "CharacterBody2D", "CharacterBody3D", "Area2D", "Area3D",
            "RigidBody2D", "RigidBody3D", "StaticBody2D", "StaticBody3D",
            "Label", "Button", "LineEdit", "TextEdit", "Panel", "VBoxContainer",
            "HBoxContainer", "GridContainer", "MarginContainer", "CenterContainer"
        ]
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute Godot-related tasks.
        
        Actions:
        - 'analyze_script': Analyze GDScript code for issues
        - 'generate_node_tree': Create a scene tree structure
        - 'explain_signal': Explain signal connections
        - 'suggest_pattern': Suggest Godot design patterns
        - 'check_godot_project': Validate .godot project file
        """
        if action == "analyze_script":
            return self.analyze_gdscript(kwargs.get("code", ""))
        elif action == "generate_node_tree":
            return self.generate_node_tree(kwargs.get("scene_type", "main"))
        elif action == "explain_signal":
            return self.explain_signal(kwargs.get("signal_name", ""), kwargs.get("context", ""))
        elif action == "suggest_pattern":
            return self.suggest_pattern(kwargs.get("problem", ""))
        elif action == "check_godot_project":
            return self.check_godot_project(kwargs.get("project_path", ""))
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "analyze_script", "generate_node_tree", "explain_signal", 
                "suggest_pattern", "check_godot_project"
            ]}
    
    def analyze_gdscript(self, code: str) -> Dict[str, Any]:
        """Analyze GDScript code for common issues and best practices."""
        issues = []
        suggestions = []
        
        # Check for _ready and _process functions
        if "func _ready()" not in code and "func _process(_delta):" not in code:
            if "extends Node" in code or "extends Node2D" in code:
                suggestions.append("Consider adding _ready() for initialization logic.")
        
        # Check for signal declarations
        signal_matches = re.findall(r'signal\s+(\w+)', code)
        if signal_matches:
            suggestions.append(f"Found signals: {', '.join(signal_matches)}. Ensure they are properly connected.")
        
        # Check for proper variable typing (GDScript 4.x feature)
        var_matches = re.findall(r'var\s+(\w+)\s*:', code)
        typed_vars = len(var_matches)
        total_vars = len(re.findall(r'\bvar\s+\w+', code))
        
        if total_vars > 0 and typed_vars < total_vars:
            suggestions.append("Consider using type hints for variables (GDScript 4.x best practice).")
        
        # Check for deprecated 'yield' (should use 'await' in Godot 4)
        if re.search(r'\byield\b', code) and "await" not in code:
            issues.append("Deprecated: 'yield' keyword detected. Use 'await' in Godot 4.x")
        
        return {
            "status": "analyzed",
            "issues": issues,
            "suggestions": suggestions,
            "signal_count": len(signal_matches),
            "typed_variables": typed_vars,
            "total_variables": total_vars
        }
    
    def generate_node_tree(self, scene_type: str) -> str:
        """Generate a recommended node tree structure for common scene types."""
        trees = {
            "player_2d": """
- CharacterBody2D (Player)
  - Sprite2D
  - CollisionShape2D
  - Camera2D
  - AnimationPlayer
  - AudioStreamPlayer2D
""",
            "enemy_2d": """
- CharacterBody2D (Enemy)
  - Sprite2D
  - CollisionShape2D
  - Area2D (DetectionZone)
    - CollisionShape2D
  - HealthBar (Control)
    - ProgressBar
""",
            "main_menu": """
- Control (MainMenu)
  - Panel
    - VBoxContainer
      - Label (Title)
      - Button (Play)
      - Button (Options)
      - Button (Quit)
  - AudioStreamPlayer (BGM)
""",
            "level": """
- Node2D (Level)
  - TileMapLayer (Terrain)
  - YSort
    - Player (CharacterBody2D)
    - Enemy1 (CharacterBody2D)
    - Enemy2 (CharacterBody2D)
  - Camera2D
  - CanvasLayer (UI)
    - HealthBar
    - ScoreLabel
"""
        }
        return trees.get(scene_type, "Scene type not recognized. Available: player_2d, enemy_2d, main_menu, level")
    
    def explain_signal(self, signal_name: str, context: str) -> str:
        """Explain how to implement and connect a specific signal."""
        explanation = f"""
Signal: {signal_name}
Context: {context}

In Godot 4.x, signals are implemented as follows:

1. Declaration (in the emitting node):
   signal {signal_name}(optional_arg: Type)

2. Emitting:
   emit_signal("{signal_name}", arg_value)
   # Or simplified: {signal_name}.emit(arg_value)

3. Connecting (in the receiver):
   $EmitterNode.{signal_name}.connect(_on_{signal_name}_received)

4. Handler function:
   func _on_{signal_name}_received(arg: Type):
       # Handle the signal
       pass

Best Practice: Use typed signals and follow the _on_<node>_<signal> naming convention.
"""
        return explanation
    
    def suggest_pattern(self, problem: str) -> str:
        """Suggest Godot design patterns based on the problem description."""
        problem_lower = problem.lower()
        
        if "state" in problem_lower or "animation" in problem_lower:
            return """
Pattern: State Machine
Use Case: Managing character states (idle, walk, jump, attack)

Implementation:
- Create a State base class with enter(), exit(), update() methods
- Create concrete state classes (IdleState, WalkState, etc.)
- Use a StateMachine node to manage transitions
- Leverage Godot's AnimationTree for visual state machines

Example:
```gdscript
class_name State
func enter(): pass
func exit(): pass
func update(delta): pass
```
"""
        elif "singleton" in problem_lower or "global" in problem_lower:
            return """
Pattern: Autoload Singleton
Use Case: Global managers (GameManager, AudioManager, SaveSystem)

Implementation:
- Create a script with `class_name GameManager`
- Go to Project Settings > Autoloads
- Add the script as an autoload
- Access globally via `GameManager.some_method()`
"""
        elif "event" in problem_lower or "communication" in problem_lower:
            return """
Pattern: Signal Bus
Use Case: Decoupled communication between distant nodes

Implementation:
- Create an Autoload script called "SignalBus"
- Declare all global signals in it
- Nodes emit/connect to SignalBus instead of direct references

Example:
```gdscript
# SignalBus.gd
extends Node
signal player_died
signal score_changed(new_score: int)
```
"""
        else:
            return "Describe your specific problem (state management, global data, events, etc.) for pattern suggestions."
    
    def check_godot_project(self, project_path: str) -> Dict[str, Any]:
        """Check if a directory contains a valid Godot project."""
        if not os.path.exists(project_path):
            return {"valid": False, "error": "Path does not exist"}
        
        godot_file = os.path.join(project_path, "project.godot")
        if not os.path.exists(godot_file):
            return {"valid": False, "error": "No project.godot file found"}
        
        # Read and parse basic info
        with open(godot_file, 'r') as f:
            content = f.read()
        
        config_version = "unknown"
        if "config_version=" in content:
            match = re.search(r'config_version=(\d+)', content)
            if match:
                version_num = int(match.group(1))
                config_version = f"Godot 4.x (config_version={version_num})" if version_num >= 5 else f"Godot 3.x (config_version={version_num})"
        
        return {
            "valid": True,
            "path": project_path,
            "config_version": config_version,
            "has_project_file": True
        }
