"""
COM Tools: Unified Godot Master Module
Integrates knowledge from 18+ official and community Godot repositories.
Acts as a central hub for engine internals, documentation, demos, plugins, and tools.
"""

from typing import Dict, List, Any, Optional
from tools.base import BaseTool

class GodotEngineTool(BaseTool):
    """
    A comprehensive Godot Engine expert module.
    Aggregates logic from godotengine/godot, godot-docs, demo projects, 
    plugins (Steam, Voxel, Firebase), and shader collections.
    """

    def __init__(self):
        self.name = "GodotEngineTool"
        self.description = "Expert system for Godot 4.x development, integrating knowledge from 18+ core repos including engine source, docs, demos, and plugins."
        
        # Knowledge Base Mapping: Repository -> Purpose
        self.knowledge_sources = {
            "core": {
                "repo": "godotengine/godot",
                "url": "https://github.com/godotengine/godot",
                "focus": "Engine source code, C++ internals, scene tree architecture, rendering pipeline."
            },
            "docs": {
                "repo": "godotengine/godot-docs",
                "url": "https://github.com/godotengine/godot-docs",
                "focus": "Official class reference, step-by-step tutorials, migration guides."
            },
            "cpp_bindings": {
                "repo": "godotengine/godot-cpp",
                "url": "https://github.com/godotengine/godot-cpp",
                "focus": "GDExtension C++ bindings, custom module development."
            },
            "learning_demos": [
                {"repo": "godotengine/godot-demo-projects", "url": "https://github.com/godotengine/godot-demo-projects", "focus": "Official feature demonstrations"},
                {"repo": "gdquest-demos/godot-3-demos", "url": "https://github.com/gdquest-demos/godot-3-demos", "focus": "GDQuest best practices & patterns"},
                {"repo": "gdquest-demos/godot-open-rpg", "url": "https://github.com/gdquest-demos/godot-open-rpg", "focus": "Complete RPG architecture reference"},
                {"repo": "KenneyNL/Starter-Kit-3D-Platformer", "url": "https://github.com/KenneyNL/Starter-Kit-3D-Platformer", "focus": "3D Platformer mechanics template"},
                {"repo": "zfoo-project/godot-start", "url": "https://github.com/zfoo-project/godot-start", "focus": "Beginner starter templates"}
            ],
            "plugins_integrations": [
                {"repo": "GodotSteam/GodotSteam", "url": "https://github.com/GodotSteam/GodotSteam", "focus": "Steamworks API integration"},
                {"repo": "zylann/godot_voxel", "url": "https://github.com/Zylann/godot_voxel", "focus": "Voxel terrain and meshing"},
                {"repo": "GodotNuts/GodotFirebase", "url": "https://github.com/GodotNuts/GodotFirebase", "focus": "Firebase backend services"},
                {"repo": "2Retr0/GodotOceanWaves", "url": "https://github.com/2Retr0/GodotOceanWaves", "focus": "FFT Ocean simulation"}
            ],
            "shaders_graphics": [
                {"repo": "gdquest-demos/godot-shaders", "url": "https://github.com/gdquest-demos/godot-shaders", "focus": "Shader library & snippets"},
                {"repo": "lettier/3d-game-shaders-for-beginners", "url": "https://github.com/lettier/3d-game-shaders-for-beginners", "focus": "Educational shader implementations"}
            ],
            "tools_utilities": [
                {"repo": "Coding-Solo/godot-mcp", "url": "https://github.com/Coding-Solo/godot-mcp", "focus": "Model Context Protocol for AI agents"},
                {"repo": "GDRETools/gdsdecomp", "url": "https://github.com/GDRETools/gdsdecomp", "focus": "Decompiling and reversing .pck/.exe"},
                {"repo": "mbrlabs/Lorien", "url": "https://github.com/mbrlabs/Lorien", "focus": "Infinite canvas whiteboard (Godot usage example)"},
                {"repo": "godotengine/awesome-godot", "url": "https://github.com/godotengine/awesome-godot", "focus": "Curated list of resources & plugins"}
            ]
        }

    def get_capabilities(self) -> List[str]:
        return [
            "analyze_gdscript",
            "explain_engine_architecture",
            "find_demo_pattern",
            "suggest_plugin",
            "generate_shader_snippet",
            "debug_scene_tree",
            "cpp_extension_guide",
            "optimize_performance"
        ]

    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Routes requests to specific Godot knowledge handlers.
        """
        if action == "analyze_gdscript":
            return self._analyze_script(kwargs.get("code", ""))
        elif action == "explain_engine_architecture":
            return self._explain_architecture(kwargs.get("topic", "SceneTree"))
        elif action == "find_demo_pattern":
            return self._find_pattern(kwargs.get("mechanic", "player_controller"))
        elif action == "suggest_plugin":
            return self._suggest_plugin(kwargs.get("feature", "steam"))
        elif action == "generate_shader_snippet":
            return self._generate_shader(kwargs.get("effect", "outline"))
        elif action == "debug_scene_tree":
            return self._debug_scene(kwargs.get("error", ""))
        elif action == "cpp_extension_guide":
            return self._cpp_guide(kwargs.get("class_name", ""))
        elif action == "optimize_performance":
            return self._optimize_performance(kwargs.get("bottleneck", "draw_calls"))
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _analyze_script(self, code: str) -> Dict[str, Any]:
        """Analyzes GDScript for Godot 4.x best practices."""
        issues = []
        suggestions = []
        
        # Basic Godot 4.x checks
        if "extends Spatial" in code:
            issues.append("Deprecated: 'Spatial' is now 'Node3D' in Godot 4.x")
            suggestions.append("Replace 'extends Spatial' with 'extends Node3D'")
        
        if "onready var" in code:
            issues.append("Syntax Update: 'onready var' is now '@onready'")
            suggestions.append("Use '@onready var variable_name = $Path'")
            
        if "_ready" in code and "super._ready()" not in code:
            suggestions.append("Consider calling 'super._ready()' if overriding ready in a subclass")

        # Check for signal syntax
        if "signal " in code and ":" not in code.split("signal ")[-1].split("\n")[0]:
             suggestions.append("Godot 4.x allows typed signals: signal hit(damage: int)")

        return {
            "success": True,
            "source": "godotengine/godot + godotengine/godot-docs",
            "analysis": {
                "issues": issues,
                "suggestions": suggestions,
                "version_target": "Godot 4.x"
            }
        }

    def _explain_architecture(self, topic: str) -> Dict[str, Any]:
        """Explains core engine concepts."""
        topics = {
            "SceneTree": {
                "description": "The SceneTree is the heart of Godot. Everything is a Node arranged in a tree structure.",
                "key_nodes": ["Node", "Node2D", "Node3D", "Control", "Resource"],
                "source": "godotengine/godot (scene/main/scene_tree.cpp)"
            },
            "Signals": {
                "description": "Observer pattern implementation. Nodes emit signals, others connect to them.",
                "syntax": "signal_name.connect(callable) / @onready var btn = $Btn; btn.pressed.connect(_on_btn_pressed)",
                "source": "godotengine/godot-docs"
            },
            "GDExtension": {
                "description": "The modern way to write C++ plugins (replacing GDNative).",
                "repo": "godotengine/godot-cpp",
                "usage": "Compile C++ code into a .gdextension file loaded by the engine."
            }
        }
        
        result = topics.get(topic, {"error": f"Topic '{topic}' not found in core knowledge base."})
        if "error" not in result:
            result["source"] = self.knowledge_sources["core"]["repo"]
            
        return {"success": True, "data": result}

    def _find_pattern(self, mechanic: str) -> Dict[str, Any]:
        """Finds relevant demo projects or code patterns."""
        mechanic = mechanic.lower()
        
        recommendations = []
        
        if "platformer" in mechanic or "movement" in mechanic:
            recommendations.append({
                "repo": "KenneyNL/Starter-Kit-3D-Platformer",
                "reason": "Complete 3D character controller with physics."
            })
            recommendations.append({
                "repo": "gdquest-demos/godot-3-demos",
                "reason": "Look for 'character-controller' folders for 2D/3D movement."
            })
            
        if "rpg" in mechanic or "inventory" in mechanic:
            recommendations.append({
                "repo": "gdquest-demos/godot-open-rpg",
                "reason": "Full inventory, dialogue, and quest system architecture."
            })
            
        if "voxel" in mechanic or "terrain" in mechanic:
            recommendations.append({
                "repo": "Zylann/godot_voxel",
                "reason": "Industry standard voxel module for Godot."
            })
            
        if "ocean" in mechanic or "water" in mechanic:
            recommendations.append({
                "repo": "2Retr0/GodotOceanWaves",
                "reason": "FFT-based ocean simulation shader and logic."
            })

        if not recommendations:
            recommendations.append({
                "repo": "godotengine/godot-demo-projects",
                "reason": "Check official demos for generic implementations."
            })

        return {"success": True, "patterns": recommendations}

    def _suggest_plugin(self, feature: str) -> Dict[str, Any]:
        """Suggests plugins based on feature request."""
        feature = feature.lower()
        
        plugins = []
        
        if "steam" in feature:
            plugins.append({"name": "GodotSteam", "repo": "GodotSteam/GodotSteam", "desc": "Full Steamworks API wrapper."})
        
        if "firebase" in feature or "backend" in feature:
            plugins.append({"name": "GodotFirebase", "repo": "GodotNuts/GodotFirebase", "desc": "Auth, Database, Storage integration."})
            
        if "voxel" in feature:
            plugins.append({"name": "Godot Voxel", "repo": "Zylann/godot_voxel", "desc": "Fast voxel streaming and meshing."})
            
        if "list" in feature or "resource" in feature:
            plugins.append({"name": "Awesome Godot", "repo": "godotengine/awesome-godot", "desc": "Search here for community plugins."})
            
        return {"success": True, "plugins": plugins}

    def _generate_shader(self, effect: str) -> Dict[str, Any]:
        """Generates basic shader snippets based on common effects."""
        effect = effect.lower()
        
        shaders = {
            "outline": """
// Godot 4.x Outline Shader (Post-Process or Edge Detect)
shader_type canvas_item;

void fragment() {
    // Simple edge detection logic placeholder
    // Refer to: gdquest-demos/godot-shaders for full implementations
    COLOR = texture(TEXTURE, UV);
}
""",
            "fresnel": """
shader_type spatial;

void fragment() {
    vec3 normal = normalize(NORMAL);
    vec3 view_dir = normalize(camera_position - WORLD_POSITION);
    float fresnel = dot(normal, view_dir);
    fresnel = clamp(1.0 - fresnel, 0.0, 1.0);
    ALBEDO = mix(vec3(1.0), vec3(0.0), fresnel); 
}
""",
            "dissolve": """
shader_type spatial;

uniform float burn_threshold : hint_range(0.0, 1.0) = 0.5;
uniform vec4 burn_color : hint_color = vec4(1.0, 0.5, 0.0, 1.0);

void fragment() {
    float alpha = texture(ALBEDO_TEXTURE, UV).a;
    if (alpha < burn_threshold) {
        discard;
    }
    ALBEDO = burn_color.rgb;
}
"""
        }
        
        snippet = shaders.get(effect, "// Effect not found. Check lettier/3d-game-shaders-for-beginners for tutorials.")
        
        return {
            "success": True,
            "shader_type": "Godot 4.x ShadingLanguage",
            "snippet": snippet,
            "reference": "gdquest-demos/godot-shaders"
        }

    def _debug_scene(self, error: str) -> Dict[str, Any]:
        """Common debugging strategies."""
        strategies = []
        
        if "null instance" in error.lower() or "nil" in error.lower():
            strategies.append("Check if nodes are assigned in @onready or via export vars.")
            strategies.append("Ensure the node path exists in the scene tree before access.")
            strategies.append("Reference: godotengine/godot-docs (Debugging page)")
            
        if "signal" in error.lower():
            strategies.append("Verify signal spelling and connection syntax: signal.connect(func)")
            
        if "shader" in error.lower():
            strategies.append("Check for Godot 4.x shader language changes (e.g., 'SCREEN_UV' vs 'SCREEN_UV')")
            strategies.append("Reference: gdquest-demos/godot-shaders")

        return {"success": True, "strategies": strategies}

    def _cpp_guide(self, class_name: str) -> Dict[str, Any]:
        """Guide for creating C++ GDExtensions."""
        return {
            "success": True,
            "guide": f"To create a C++ class '{class_name}':",
            "steps": [
                "1. Setup godot-cpp bindings (repo: godotengine/godot-cpp)",
                "2. Inherit from godot::Node or godot::RefCounted",
                "3. Use GDCLASS(MyClass, ParentClass) macro",
                "4. Register methods in _bind_methods()",
                "5. Compile to .gdextension and load in Godot"
            ],
            "example_repo": "godotengine/godot-cpp"
        }

    def _optimize_performance(self, bottleneck: str) -> Dict[str, Any]:
        """Performance tips based on bottleneck."""
        tips = []
        
        if "draw" in bottleneck or "render" in bottleneck:
            tips.append("Use Occlusion Culling (Godot 4.x feature).")
            tips.append("Batch draw calls by using AtlasTextures.")
            tips.append("Reduce overdraw in shaders.")
            
        if "physics" in bottleneck:
            tips.append("Use Collision Layers/Masks to reduce collision checks.")
            tips.append("Switch to KinematicCharacter if rigid body isn't needed.")
            
        if "memory" in bottleneck:
            tips.append("Use ResourceLoader.load_async() for large assets.")
            tips.append("Avoid creating objects in _process(); reuse instances.")

        return {
            "success": True,
            "bottleneck": bottleneck,
            "tips": tips,
            "reference": "godotengine/godot-docs (Optimization guidelines)"
        }
