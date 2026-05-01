extends CharacterBody2D

# INTENTIONAL ERROR 1: Typo in signal name (should be "hit", not "hits")
signal hits # Wrong signal name

# INTENTIONAL ERROR 2: References non-existent node path
@onready var hit_box = $HitBox  # HitBox doesn't exist in scene

# INTENTIONAL ERROR 3: Wrong type hint
var speed: int = 400.0  # Should be float

# INTENTIONAL ERROR 4: Missing signal connection
func _ready():
    # Should connect to a signal but doesn't
    pass

func _physics_process(delta):
    # INTENTIONAL ERROR 5: Undefined variable
    velocity.x = input_direction * speedd  # Typo: speedd instead of speed
    
    move_and_slide()

# INTENTIONAL ERROR 6: Function signature mismatch
func take_damage(amount, extra_param):
    # Godot signal only passes one parameter
    health -= amount

# INTENTIONAL ERROR 7: Accessing property on null
func get_player_pos():
    return $MissingNode.position  # MissingNode doesn't exist

# INTENTIONAL ERROR 8: Incorrect use of await
func load_resource():
    var resource = await load("res://nonexistent.tscn")  # File doesn't exist
    return resource

# INTENTIONAL ERROR 9: Array index out of bounds
func get_first_item(items: Array):
    return items[0]  # No bounds check

# INTENTIONAL ERROR 10: Division by zero potential
func calculate_ratio(a, b):
    return a / b  # No check if b is zero
