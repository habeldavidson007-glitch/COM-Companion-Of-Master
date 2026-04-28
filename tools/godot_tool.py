"""
COM SGMA LIGHT - Godot Tool
============================
Phase 2d: GDScript template generation for Godot Engine.
Generates movement scripts (2D/3D) and animation templates.
"""

import os

# Pre-built script templates
TEMPLATES = {
    "MOV:2D": """extends CharacterBody2D

const SPEED = 200.0

func _physics_process(delta):
    var direction = Vector2.ZERO
    if Input.is_action_pressed("ui_right"): direction.x += 1
    if Input.is_action_pressed("ui_left"):  direction.x -= 1
    if Input.is_action_pressed("ui_down"):  direction.y += 1
    if Input.is_action_pressed("ui_up"):    direction.y -= 1
    velocity = direction.normalized() * SPEED
    move_and_slide()
""",

    "MOV:3D": """extends CharacterBody3D

const SPEED = 5.0

func _physics_process(delta):
    var direction = Vector3.ZERO
    if Input.is_action_pressed("ui_right"): direction.x += 1
    if Input.is_action_pressed("ui_left"):  direction.x -= 1
    if Input.is_action_pressed("ui_forward"): direction.z -= 1
    if Input.is_action_pressed("ui_back"):    direction.z += 1
    velocity = direction.normalized() * SPEED
    move_and_slide()
""",

    "ANIM:IDLE": """extends AnimationPlayer

func _ready():
    play("idle")

func set_state(state: String):
    if has_animation(state):
        play(state)
""",
}


def run(payload: str) -> str:
    """
    Generate GDScript files from templates.

    Payload format: CATEGORY:DETAIL
    Example: MOV:2D  |  ANIM:IDLE  |  SCENE:PLAYER

    Args:
        payload: String containing category and detail for script generation

    Returns:
        Status string indicating success or failure
    """
    try:
        key = payload.strip().upper()

        if key in TEMPLATES:
            script = TEMPLATES[key]
            filename = f"com_{key.replace(':', '_').lower()}.gd"
            with open(filename, "w") as f:
                f.write(script)
            return f"✅ GDScript saved: {filename}"
        else:
            # Unknown template — save raw payload as script
            filename = "com_output.gd"
            with open(filename, "w") as f:
                f.write(payload)
            return f"✅ GDScript saved: {filename} (raw)"

    except Exception as e:
        return f"❌ Godot tool failed: {str(e)}"
