"""
Large utility file for token testing.
Contains many functions to test context compression.
"""
extends Node

# Utility constants
const MAX_HEALTH = 100
const MIN_HEALTH = 0
const GRAVITY = 9.8
const JUMP_FORCE = -400
const MOVE_SPEED = 300
const DASH_SPEED = 600
const FRICTION = 0.8
const AIR_RESISTANCE = 0.9
const GROUND_ACCELERATION = 5.0
const AIR_ACCELERATION = 2.5
const MAX_FALL_SPEED = 800
const COYOTE_TIME = 0.1
const JUMP_BUFFER = 0.1
const DOUBLE_JUMP_ENABLED = true
const WALL_JUMP_ENABLED = true
const WALL_SLIDE_SPEED = 200
const WALL_JUMP_FORCE = Vector2(300, -350)
const DASH_DURATION = 0.15
const DASH_COOLDOWN = 0.5
const INVINCIBILITY_TIME = 1.0
const ATTACK_RANGE = 50
const ATTACK_DAMAGE = 10
const ATTACK_COOLDOWN = 0.3
const CRITICAL_HIT_CHANCE = 0.1
const CRITICAL_HIT_MULTIPLIER = 2.0
const EXPERIENCE_MULTIPLIER = 1.5
const GOLD_DROP_CHANCE = 0.3
const ITEM_DROP_CHANCE = 0.1
const ENEMY_SPAWN_INTERVAL = 2.0
const MAX_ENEMIES = 10
const LEVEL_BOUNDS = Rect2(-1000, -500, 2000, 1000)
const CAMERA_SMOOTHING = 0.1
const CAMERA_DEADZONE = Vector2(100, 50)
const SCREEN_SHAKE_INTENSITY = 5.0
const PARTICLE_COUNT = 20
const AUDIO_BUS_MASTER = "Master"
const AUDIO_BUS_SFX = "SFX"
const AUDIO_BUS_MUSIC = "Music"
const VOLUME_DB_MIN = -80.0
const VOLUME_DB_MAX = 6.0
const SAVE_FILE_PATH = "user://savegame.dat"
const CONFIG_FILE_PATH = "user://config.json"
const LOG_FILE_PATH = "user://game.log"

# Helper functions
func clamp_value(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))

func lerp_vector2(from: Vector2, to: Vector2, t: float) -> Vector2:
    return Vector2(lerp(from.x, to.x, t), lerp(from.y, to.y, t))

func normalize_vector2(vec: Vector2) -> Vector2:
    if vec.length() == 0:
        return Vector2.ZERO
    return vec.normalized()

func distance_to(from: Vector2, to: Vector2) -> float:
    return from.distance_to(to)

func angle_to(from: Vector2, to: Vector2) -> float:
    return from.angle_to_point(to)

func direction_to(from: Vector2, to: Vector2) -> Vector2:
    return (to - from).normalized()

func random_range(min_val: float, max_val: float) -> float:
    return randf_range(min_val, max_val)

func random_int_range(min_val: int, max_val: int) -> int:
    return randi_range(min_val, max_val)

func chance(probability: float) -> bool:
    return randf() < probability

func load_resource(path: String) -> Resource:
    return load(path)

func instantiate_scene(path: String) -> Node:
    var scene = load(path)
    if scene:
        return scene.instantiate()
    return null

func get_node_or_null(parent: Node, path: String) -> Node:
    if parent.has_node(path):
        return parent.get_node(path)
    return null

func safe_connect(signal_name: String, callable: Callable) -> Error:
    # Placeholder for safe signal connection logic
    return OK

func format_number(num: float, decimals: int = 0) -> String:
    if decimals > 0:
        return str(snapped(num, pow(0.1, decimals)))
    return str(int(num))

func seconds_to_time(seconds: float) -> String:
    var mins = int(seconds / 60)
    var secs = int(seconds) % 60
    return "%02d:%02d" % [mins, secs]

func get_timestamp() -> String:
    var time = Time.get_datetime_dict_from_system()
    return "%04d-%02d-%02d_%02d-%02d-%02d" % [
        time.year, time.month, time.day,
        time.hour, time.minute, time.second
    ]

func log_message(message: String, level: String = "INFO") -> void:
    var timestamp = get_timestamp()
    print("[%s] %s: %s" % [timestamp, level, message])

func save_data(data: Dictionary, path: String) -> Error:
    var file = FileAccess.open(path, FileAccess.WRITE)
    if file:
        file.store_var(data)
        file.close()
        return OK
    return ERR_CANT_CREATE

func load_data(path: String) -> Variant:
    if not FileAccess.file_exists(path):
        return null
    var file = FileAccess.open(path, FileAccess.READ)
    if file:
        return file.get_var()
    return null

func delete_file(path: String) -> Error:
    return DirAccess.remove_absolute(path)

func directory_exists(path: String) -> bool:
    return DirAccess.dir_exists_absolute(path)

func create_directory(path: String) -> Error:
    return DirAccess.make_dir_recursive_absolute(path)

func get_files_in_directory(dir_path: String, extension: String = "") -> PackedStringArray:
    var files: PackedStringArray = []
    var dir = DirAccess.open(dir_path)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if not dir.current_is_dir():
                if extension == "" or file_name.ends_with(extension):
                    files.append(dir_path + "/" + file_name)
            file_name = dir.get_next()
        dir.list_dir_end()
    return files

func play_sound(sound_name: String, bus: String = AUDIO_BUS_SFX) -> void:
    # Placeholder for sound playback
    pass

func stop_all_sounds() -> void:
    # Placeholder for stopping all sounds
    pass

func set_volume(bus: String, volume_db: float) -> void:
    AudioServer.set_bus_volume_db(AudioServer.get_bus_index(bus), clamp(volume_db, VOLUME_DB_MIN, VOLUME_DB_MAX))

func get_volume(bus: String) -> float:
    var bus_idx = AudioServer.get_bus_index(bus)
    if bus_idx >= 0:
        return AudioServer.get_bus_volume_db(bus_idx)
    return VOLUME_DB_MIN

func mute_bus(bus: String, muted: bool) -> void:
    var bus_idx = AudioServer.get_bus_index(bus)
    if bus_idx >= 0:
        AudioServer.set_bus_mute(bus_idx, muted)

func is_bus_muted(bus: String) -> bool:
    var bus_idx = AudioServer.get_bus_index(bus)
    if bus_idx >= 0:
        return AudioServer.is_bus_mute(bus_idx)
    return false

func create_particle_effect(count: int = PARTICLE_COUNT) -> GPUParticles2D:
    var particles = GPUParticles2D.new()
    particles.amount = count
    return particles

func create_tween() -> Tween:
    return create_tween()

func shake_camera(intensity: float = SCREEN_SHAKE_INTENSITY, duration: float = 0.5) -> void:
    # Placeholder for camera shake
    pass

func freeze_game(duration: float) -> void:
    # Placeholder for game freeze
    pass

func unpause_game() -> void:
    get_tree().paused = false

func pause_game() -> void:
    get_tree().paused = true

func is_game_paused() -> bool:
    return get_tree().paused

func change_scene(path: String) -> Error:
    return get_tree().change_scene_to_file(path)

func reload_current_scene() -> Error:
    return get_tree().reload_current_scene()

func quit_game() -> void:
    get_tree().quit()

func get_fps() -> int:
    return Engine.get_frames_per_second()

func set_max_fps(fps: int) -> void:
    Engine.max_fps = fps

func is_debug_build() -> bool:
    return OS.is_debug_build()

func get_platform_name() -> String:
    return OS.get_name()

func is_mobile_platform() -> bool:
    var platform = get_platform_name()
    return platform in ["Android", "iOS"]

func is_desktop_platform() -> bool:
    var platform = get_platform_name()
    return platform in ["Windows", "macOS", "Linux", "FreeBSD", "NetBSD", "OpenBSD", "BSD"]

func is_web_platform() -> bool:
    return get_platform_name() == "Web"

func request_permission(permission: String) -> bool:
    return OS.request_permission(permission)

func has_permission(permission: String) -> bool:
    return OS.has_permission(permission)

func clipboard_set(text: String) -> void:
    DisplayServer.clipboard_set(text)

func clipboard_get() -> String:
    return DisplayServer.clipboard_get()

func set_window_title(title: String) -> void:
    DisplayServer.window_set_title(title)

func get_window_size() -> Vector2:
    return DisplayServer.window_get_size()

func set_window_size(size: Vector2) -> void:
    DisplayServer.window_set_size(size)

func center_window() -> void:
    var screen_size = DisplayServer.screen_get_size()
    var window_size = get_window_size()
    DisplayServer.window_set_position((screen_size - window_size) / 2)

func is_window_focused() -> bool:
    return DisplayServer.window_has_focus()

func vibrate_device(duration_ms: int = 100) -> void:
    Input.start_joy_vibration(0, 0, 0.5, duration_ms / 1000.0)

func stop_vibration() -> void:
    Input.stop_joy_vibration(0)

func is_controller_connected() -> bool:
    return Input.get_connected_joypads().size() > 0

func get_controller_count() -> int:
    return Input.get_connected_joypads().size()

func get_player_input(player_id: int = 0) -> Vector2:
    var input = Vector2.ZERO
    input.x = Input.get_axis("ui_left", "ui_right")
    input.y = Input.get_axis("ui_up", "ui_down")
    return input

func is_action_just_pressed(action: String, player_id: int = 0) -> bool:
    return Input.is_action_just_pressed(action)

func is_action_pressed(action: String, player_id: int = 0) -> bool:
    return Input.is_action_pressed(action)

func get_mouse_position() -> Vector2:
    return get_viewport().get_mouse_position()

func is_mouse_over_rect(rect: Rect2) -> bool:
    return rect.has_point(get_mouse_position())

func world_to_screen(world_pos: Vector2) -> Vector2:
    return get_viewport().get_camera_2d().unproject_position(world_pos)

func screen_to_world(screen_pos: Vector2) -> Vector2:
    return get_viewport().get_camera_2d().project_position(screen_pos)

func draw_debug_line(from: Vector2, to: Vector2, color: Color = Color.RED, width: float = 1.0) -> void:
    # Debug drawing placeholder
    pass

func draw_debug_circle(pos: Vector2, radius: float, color: Color = Color.GREEN) -> void:
    # Debug drawing placeholder
    pass

func draw_debug_rect(rect: Rect2, color: Color = Color.BLUE, filled: bool = false) -> void:
    # Debug drawing placeholder
    pass

func clear_debug_drawings() -> void:
    # Clear debug drawings placeholder
    pass

# More utility functions to increase file size for token testing
func calculate_damage(base_damage: float, modifiers: Dictionary) -> float:
    var damage = base_damage
    if modifiers.has("strength"):
        damage *= 1.0 + modifiers.strength * 0.01
    if modifiers.has("critical") and modifiers.critical:
        damage *= CRITICAL_HIT_MULTIPLIER
    return floor(damage)

func apply_status_effect(target: Node, effect: String, duration: float) -> void:
    # Placeholder for status effect application
    pass

func remove_status_effect(target: Node, effect: String) -> void:
    # Placeholder for status effect removal
    pass

func has_status_effect(target: Node, effect: String) -> bool:
    # Placeholder for status effect check
    return false

func spawn_enemy(enemy_type: String, position: Vector2) -> Node:
    # Placeholder for enemy spawning
    return null

func despawn_enemy(enemy: Node) -> void:
    # Placeholder for enemy despawning
    pass

func get_nearest_enemy(position: Vector2, max_distance: float = INF) -> Node:
    # Placeholder for finding nearest enemy
    return null

func get_enemies_in_radius(position: Vector2, radius: float) -> Array:
    # Placeholder for finding enemies in radius
    return []

func check_collision(shape: Shape2D, transform: Transform2D, exclude: Array = []) -> bool:
    # Placeholder for collision checking
    return false

func raycast(from: Vector2, to: Vector2, mask: int = 1) -> Dictionary:
    # Placeholder for raycasting
    return {"hit": false}

func overlap_area(shape: Shape2D, transform: Transform2D) -> Array:
    # Placeholder for area overlap detection
    return []

func move_character(character: CharacterBody2D, velocity: Vector2) -> bool:
    character.velocity = velocity
    return character.move_and_slide()

func snap_to_grid(position: Vector2, grid_size: int = 32) -> Vector2:
    return Vector2(
        round(position.x / grid_size) * grid_size,
        round(position.y / grid_size) * grid_size
    )

func is_on_grid(position: Vector2, grid_size: int = 32) -> bool:
    return snap_to_grid(position, grid_size) == position

func get_tile_at_position(position: Vector2, tilemap: TileMap) -> Vector2i:
    return tilemap.local_to_map(position)

func get_tile_position(tile_coord: Vector2i, tilemap: TileMap) -> Vector2:
    return tilemap.map_to_local(tile_coord)

func set_tile(tilemap: TileMap, coord: Vector2i, tile_id: int) -> void:
    tilemap.set_cell(0, coord, tile_id)

func get_tile(tilemap: TileMap, coord: Vector2i) -> int:
    return tilemap.get_cell_source_id(0, coord)

func erase_tile(tilemap: TileMap, coord: Vector2i) -> void:
    tilemap.erase_cell(0, coord)

func interpolate_color(from: Color, to: Color, t: float) -> Color:
    return Color(
        lerp(from.r, to.r, t),
        lerp(from.g, to.g, t),
        lerp(from.b, to.b, t),
        lerp(from.a, to.a, t)
    )

func color_from_hex(hex: String) -> Color:
    hex = hex.trim_prefix("#")
    if hex.length() == 6:
        return Color8(
            int(hex.substr(0, 2), 16),
            int(hex.substr(2, 2), 16),
            int(hex.substr(4, 2), 16)
        )
    return Color.WHITE

func color_to_hex(color: Color) -> String:
    return "#%02X%02X%02X" % [int(color.r * 255), int(color.g * 255), int(color.b * 255)]

func ease_in_out(t: float) -> float:
    return t * t * (3.0 - 2.0 * t * t)

func ease_in_quad(t: float) -> float:
    return t * t

func ease_out_quad(t: float) -> float:
    return 1.0 - (1.0 - t) * (1.0 - t)

func ease_in_cubic(t: float) -> float:
    return t * t * t

func ease_out_cubic(t: float) -> float:
    return 1.0 - pow(1.0 - t, 3)

func ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4.0 * t * t * t
    else:
        return 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0

func ping_server(url: String) -> bool:
    # Placeholder for server ping
    return true

func fetch_json(url: String) -> Dictionary:
    # Placeholder for JSON fetching
    return {}

func post_json(url: String, data: Dictionary) -> bool:
    # Placeholder for JSON posting
    return true

def encrypt_string(text: String, key: String) -> String:
    # Placeholder for encryption
    return text

func decrypt_string(encrypted: String, key: String) -> String:
    # Placeholder for decryption
    return encrypted

func hash_string(text: String) -> String:
    # Placeholder for hashing
    return text.hash()

func compress_data(data: PackedByteArray) -> PackedByteArray:
    # Placeholder for compression
    return data

func decompress_data(compressed: PackedByteArray) -> PackedByteArray:
    # Placeholder for decompression
    return compressed

func base64_encode(data: PackedByteArray) -> String:
    return Marshalls.raw_to_base64(data)

func base64_decode(encoded: String) -> PackedByteArray:
    return Marshalls.base64_to_raw(encoded)

func uuid_generate() -> String:
    # Simple UUID-like generator placeholder
    return "%08x-%04x-%04x-%04x-%012x" % [randi(), randi() % 0xFFFF, randi() % 0xFFFF, randi() % 0xFFFF, randi()]

func performance_mark(label: String) -> void:
    # Placeholder for performance marking
    pass

func performance_measure(start_label: String, end_label: String) -> float:
    # Placeholder for performance measurement
    return 0.0

func memory_usage() -> int:
    # Return approximate memory usage
    return Performance.get_monitor(Performance.MEMORY_STATIC)

func object_count() -> int:
    return Performance.get_monitor(Performance.OBJECT_COUNT)

func render_batch_count() -> int:
    return Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)

func physics_frame_time() -> float:
    return Performance.get_monitor(Performance.PHYSICS_FRAME_TIME) * 1000.0

func process_frame_time() -> float:
    return Performance.get_monitor(Performance.PROCESS_FRAME_TIME) * 1000.0

func total_frame_time() -> float:
    return Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0

func reset_performance_monitors() -> void:
    Performance.reset_monitors()

func enable_profiling(enabled: bool) -> void:
    # Placeholder for enabling/disabling profiling
    pass

func export_profile(path: String) -> Error:
    # Placeholder for profile export
    return OK

func import_profile(path: String) -> Dictionary:
    # Placeholder for profile import
    return {}

func validate_save_data(data: Dictionary) -> bool:
    # Validate save data structure
    return data.has("player") and data.has("level")

func migrate_save_data(old_data: Dictionary) -> Dictionary:
    # Migrate old save data to new format
    return old_data

func backup_save_file(source: String, backup_suffix: String = ".bak") -> Error:
    if FileAccess.file_exists(source):
        return DirAccess.copy_absolute(source, source + backup_suffix)
    return ERR_FILE_NOT_FOUND

func restore_save_file(source: String, backup_suffix: String = ".bak") -> Error:
    var backup_path = source + backup_suffix
    if FileAccess.file_exists(backup_path):
        return DirAccess.copy_absolute(backup_path, source)
    return ERR_FILE_NOT_FOUND

func cleanup_backup_files(directory: String, backup_suffix: String = ".bak") -> int:
    var cleaned = 0
    var files = get_files_in_directory(directory)
    for file in files:
        if file.ends_with(backup_suffix):
            if delete_file(file) == OK:
                cleaned += 1
    return cleaned

func get_free_disk_space(path: String = "user://") -> int:
    # Placeholder for disk space check
    return 1073741824  # 1GB fake value

func get_total_disk_space(path: String = "user://") -> int:
    # Placeholder for total disk space
    return 10737418240  # 10GB fake value

func is_disk_space_low(threshold_mb: int = 100) -> bool:
    return get_free_disk_space() < threshold_mb * 1024 * 1024

func schedule_cleanup(delay_seconds: float) -> void:
    # Placeholder for scheduled cleanup
    pass

func cancel_scheduled_cleanup() -> void:
    # Placeholder for canceling scheduled cleanup
    pass

func run_gc() -> void:
    # Force garbage collection placeholder
    pass

func optimize_memory() -> void:
    # Memory optimization placeholder
    run_gc()
    clear_debug_drawings()

func get_system_info() -> Dictionary:
    return {
        "platform": get_platform_name(),
        "debug": is_debug_build(),
        "fps": get_fps(),
        "memory_mb": memory_usage() / 1024 / 1024,
        "objects": object_count()
    }

func print_system_info() -> void:
    var info = get_system_info()
    log_message("System Info: %s" % str(info), "DEBUG")

func benchmark_function(func_ref: Callable, iterations: int = 100) -> float:
    var start = Time.get_ticks_usec()
    for i in range(iterations):
        func_ref.call()
    var elapsed = Time.get_ticks_usec() - start
    return elapsed / float(iterations)

func benchmark_block(label: String, func_ref: Callable) -> void:
    var start = Time.get_ticks_usec()
    func_ref.call()
    var elapsed = Time.get_ticks_usec() - start
    log_message("Benchmark [%s]: %.2f ms" % [label, elapsed / 1000.0], "DEBUG")

func warmup_cache() -> void:
    # Pre-warm frequently used resources
    pass

func preload_resources(paths: PackedStringArray) -> void:
    for path in paths:
        load_resource(path)

func unload_unused_resources() -> void:
    # Placeholder for unloading unused resources
    pass

func get_resource_cache_size() -> int:
    # Placeholder for cache size check
    return 0

func clear_resource_cache() -> void:
    # Placeholder for clearing resource cache
    pass

func report_bug(description: String, steps: Array = []) -> void:
    log_message("BUG REPORT: %s" % description, "ERROR")
    log_message("Steps: %s" % str(steps), "ERROR")

func report_crash(error: String, stack: Array = []) -> void:
    log_message("CRASH: %s" % error, "FATAL")
    log_message("Stack: %s" % str(stack), "FATAL")

func send_analytics_event(event_name: String, data: Dictionary = {}) -> void:
    # Placeholder for analytics
    pass

func track_player_action(action: String, context: Dictionary = {}) -> void:
    # Placeholder for player action tracking
    pass

func track_session_start() -> void:
    # Placeholder for session start tracking
    pass

func track_session_end() -> void:
    # Placeholder for session end tracking
    pass

func get_session_duration() -> float:
    # Placeholder for session duration
    return 0.0

func initialize_utils() -> void:
    log_message("Utils initialized", "INFO")

func shutdown_utils() -> void:
    log_message("Utils shutting down", "INFO")
    cancel_scheduled_cleanup()
    cleanup_backup_files("user://")

# End of utils.gd
