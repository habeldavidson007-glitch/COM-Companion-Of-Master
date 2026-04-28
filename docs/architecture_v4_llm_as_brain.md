# COM Architecture V4: LLM as Brain with Expert Harnesses

## Overview
This architecture implements the "LLM as Brain" concept where the LLM acts purely as an intent detector and signal router, while specialized expert modules and harnesses execute all actual work.

## Key Components

### 1. Intent Router (`core/intent_router.py`)
**Purpose**: Two-stage classification system that routes user queries to appropriate harnesses

**Features**:
- **Stage 1**: Fast keyword matching (8 modes: GODOT, OFFICE, CPP, PYTHON, JAVASCRIPT, JSON, DESKTOP, WIKI)
- **Stage 2**: LLM tie-breaker for ambiguous queries
- **Signal Generation**: Creates COM signals in format `@HARNESS:action:payload`
- **Wiki Integration**: Enhanced routing with wiki lookup for knowledge queries
- **Statistics Tracking**: Monitors routing decisions and confidence levels

**Supported Modes**:
- `GODOT`: Game development with Godot Engine
- `OFFICE`: Excel, PDF, PowerPoint operations
- `CPP`: C++ development assistance
- `PYTHON`: Python programming
- `JAVASCRIPT`: JavaScript/TypeScript development
- `JSON`: JSON parsing, validation, schema generation
- `DESKTOP`: File operations, browser control, clipboard, screenshots
- `WIKI`: Knowledge retrieval and synthesis

### 2. Expert Modules

#### JSON Expert (`tools/languages/json_expert.py`)
**Actions**:
- `validate`: Validate JSON syntax and structure
- `format`: Beautify JSON with indentation
- `minify`: Compress JSON by removing whitespace
- `transform`: Transform JSON structure based on mapping
- `extract`: Extract specific paths using dot notation
- `generate_schema`: Auto-generate JSON Schema from data
- `explain`: Explain JSON concepts (syntax, schema, validation, best practices, JSONPath)
- `compare`: Compare two JSON objects and identify differences

#### JavaScript Expert (`tools/languages/javascript_expert.py`)
**Actions**:
- `analyze_code`: Analyze JS code for issues and modern practices
- `modernize`: Suggest ES6+ improvements for legacy code
- `explain_concept`: Explain JS concepts (closures, promises, async/await, etc.)
- `generate_template`: Generate code templates (functions, classes, React components, Express routes, Jest tests)
- `check_async`: Analyze async/await usage patterns
- `convert_to_ts`: Suggest TypeScript conversions

#### C++ Expert (`tools/languages/cpp_expert.py`)
**Actions**:
- `analyze_code`: Check for memory safety, modern C++ features
- `suggest_modernization`: Convert legacy C++ to modern standards
- `explain_concept`: Smart pointers, move semantics, RAII, templates
- `generate_template`: Class templates, singletons, CMake, unit tests
- `check_memory_safety`: Detect memory leaks and unsafe patterns

#### Python Expert (`tools/languages/python_expert.py`)
Already existing - comprehensive Python development assistance

### 3. Desktop Harness (`tools/system/desktop_harness.py`)
**Purpose**: Physical desktop interaction capabilities

**Actions**:
- `open_file`: Open file with default application
- `open_folder`: Open folder in file explorer
- `open_browser`: Open URL in specified browser
- `create_file`: Create new file with content
- `create_folder`: Create directory structure
- `copy_file`: Copy files
- `move_file`: Move/rename files
- `delete_file`: Delete files (with trash support)
- `read_file`: Read file contents
- `write_file`: Write/append to files
- `list_files`: List directory contents
- `search_files`: Search files by pattern
- `run_command`: Execute system commands (with safety checks)
- `type_text`: Simulate keyboard typing
- `take_screenshot`: Capture screen
- `get_clipboard`: Read clipboard content
- `set_clipboard`: Write to clipboard
- `get_system_info`: Retrieve system information

**Security Features**:
- Blocks dangerous commands (rm -rf /, fork bombs, etc.)
- Timeout protection for long-running commands
- Platform-specific implementations (Windows, macOS, Linux)

## COM Signal Protocol

### Format
```
@HARNESS:action:payload
```

### Examples
```
@DESK:open_browser:https://google.com
@JSON:validate:{"name": "test", "value": 123}
@CPP:generate_template:class
@JS:analyze_code:function test() { return 42; }
@OFFICE:create_excel:sales_report:Q1,2024,data
@PYTHON:execute_script:print("Hello World")
@GODOT:create_scene:player_2d.tscn
@WIKI:search:what is a closure
```

### Signal Parsing
The Intent Router provides `parse_signal()` method to extract:
- `harness`: Target module (DESK, JSON, CPP, JS, etc.)
- `action`: Specific action to perform
- `payload`: Data/parameters for the action

## Architecture Benefits

### 1. Separation of Concerns
- **LLM**: Only detects intent and routes signals (Brain)
- **Harnesses**: Execute actual work (Muscles)
- **Experts**: Provide domain-specific knowledge (Specialized Skills)

### 2. Scalability
- Add new experts without modifying core logic
- Each harness can be independently improved
- No need for larger/better LLM models

### 3. Performance
- Keyword-based routing is instant
- Parallel execution of multiple harnesses
- Caching at harness level for repeated operations

### 4. Maintainability
- Clear boundaries between components
- Easy to test individual modules
- Failures isolated to specific harnesses

### 5. Security
- Desktop actions have safety checks
- Command execution filtered for dangerous patterns
- Platform-specific security measures

## Usage Example

```python
from core.intent_router import IntentRouter
from tools.languages import JsonExpertTool, JavaScriptExpertTool
from tools.system import DesktopHarness

# Initialize
router = IntentRouter()
json_tool = JsonExpertTool()
js_tool = JavaScriptExpertTool()
desk = DesktopHarness()

# User query
query = "create a JSON file with user data and open it"

# Route query
result = router.route(query)
print(f"Mode: {result['mode']}")  # JSON or DESKTOP
print(f"Signal: {result['signal']}")  # @JSON:... or @DESK:...

# Parse and execute signal
parsed = router.parse_signal(result['signal'])
harness = parsed['harness']
action = parsed['action']
payload = parsed['payload']

# Execute appropriate harness
if harness == "JSON":
    response = json_tool.execute(action, json_data=payload)
elif harness == "DESK":
    response = desk.execute(action, file_path=payload)

# Response comes from harness, not LLM
print(response)
```

## Future Enhancements

1. **More Experts**: Rust, Go, SQL, Data Science, DevOps
2. **Advanced Routing**: Context-aware, multi-step workflows
3. **Parallel Execution**: Run multiple harnesses simultaneously
4. **Learning System**: Improve routing based on success/failure feedback
5. **Plugin Architecture**: Dynamic loading of new harnesses
6. **Natural Language Signals**: More intuitive signal formats

## Conclusion

This architecture achieves the goal of making the LLM purely a "brain" that:
- Detects user intent automatically
- Routes signals to appropriate harnesses
- Never generates answers directly

All execution, output generation, and domain expertise come from specialized harnesses, allowing the system to scale with better harness design rather than requiring larger/more expensive LLM models.
