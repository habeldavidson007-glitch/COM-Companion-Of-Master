# E+ Language Dictionary & User Guide

## 📘 Overview

**E+** is a human-readable, intent-driven Domain Specific Language (DSL) designed for clarity and deterministic execution. It serves as the user-facing language for the COM IDE, translating directly into an internal **Signal IR** before execution in Python.

This guide serves as the definitive dictionary for all E+ syntax, keywords, and concepts.

---

## 🧠 Core Philosophy

1.  **Intent First**: Code expresses *what* you want, not *how* the machine does it.
2.  **Explicit Structure**: No implicit behavior; blocks and assignments are always clear.
3.  **Keyword Driven**: Meaningful words (`say`, `input`, `repeat`) over cryptic symbols.
4.  **Deterministic**: Every E+ line maps 1:1 to a specific Signal instruction.

---

## 🔑 Key Symbols

| Symbol | Name | Usage | Example |
| :--- | :--- | :--- | :--- |
| `@` | **Entity Prefix** | Marks all user-defined variables. | `@name` |
| `( )` | **Data Container** | Wraps values, expressions, or arguments. | `("Hello")`, `(@a + 1)` |
| `{ }` | **Block Scope** | Defines the body of loops, functions, or conditions. | `{ say("Hi") }` |
| `=` | **Assignment** | Assigns a value to a variable. | `@x = (10)` |
| `.` | **Property Access** | Accesses properties of an object. | `@car.color` |

---

## 📖 Keyword Dictionary

### 1. Data & Variables

#### `@` (Variable Declaration)
*   **Definition**: All variables must start with `@`.
*   **Syntax**: `@variable_name`
*   **Example**:
    ```eplus
    @score = (0)
    ```

#### `input`
*   **Definition**: Requests text input from the user.
*   **Syntax**: `@var = input("Prompt Message")`
*   **Signal Mapping**: `INPUT`
*   **Example**:
    ```eplus
    @name = input("What is your name?")
    ```

---

### 2. Output & Interaction

#### `say`
*   **Definition**: Displays output to the user (standard output).
*   **Syntax**: `say(Content)`
*   **Signal Mapping**: `OUTPUT`
*   **Example**:
    ```eplus
    say("Hello World")
    say(@name)
    say(@score + 10)
    ```

---

### 3. Control Flow

#### `if` / `else if` / `else`
*   **Definition**: Conditional execution logic.
*   **Syntax**:
    ```eplus
    if (Condition) {
        // Code block
    } else if (Condition) {
        // Code block
    } else {
        // Code block
    }
    ```
*   **Rules**:
    *   Conditions must be wrapped in `( )`.
    *   Blocks must be wrapped in `{ }`.
*   **Signal Mapping**: `IF`
*   **Example**:
    ```eplus
    if (@age > 18) {
        say("Adult")
    } else {
        say("Minor")
    }
    ```

#### `repeat` (Range Loop)
*   **Definition**: Executes a block a specific number of times.
*   **Syntax**: `repeat (@iterator, Count) { ... }`
*   **Signal Mapping**: `LOOP_RANGE`
*   **Example**:
    ```eplus
    repeat (@i, 5) {
        say(@i)
    }
    ```

#### `repeat while` (While Loop)
*   **Definition**: Executes a block while a condition is true.
*   **Syntax**: `repeat while (Condition) { ... }`
*   **Signal Mapping**: `LOOP_WHILE`
*   **Example**:
    ```eplus
    repeat while (@x > 0) {
        @x = (@x - 1)
    }
    ```

#### `break`
*   **Definition**: Immediately exits the nearest enclosing loop.
*   **Syntax**: `break`
*   **Signal Mapping**: `BREAK`

#### `exit`
*   **Definition**: Terminates the entire program execution.
*   **Syntax**: `exit`
*   **Signal Mapping**: `EXIT`

---

### 4. Functions

#### `function`
*   **Definition**: Defines a reusable block of code.
*   **Syntax**:
    ```eplus
    function FunctionName(@arg1, @arg2) {
        // Body
        return(Value)
    }
    ```
*   **Signal Mapping**: `FUNCTION_DEF`

#### `return`
*   **Definition**: Returns a value from a function.
*   **Syntax**: `return(Value)`
*   **Signal Mapping**: `RETURN`

#### `call`
*   **Definition**: Invokes a defined function.
*   **Syntax**: `@result = call FunctionName(Arg1, Arg2)`
*   **Signal Mapping**: `CALL`
*   **Example**:
    ```eplus
    function Add(@a, @b) {
        return(@a + @b)
    }

    @sum = call Add(10, 20)
    say(@sum)
    ```

---

## ⚙️ Grammar Rules (Strict)

To ensure the compiler works correctly, you must follow these rules:

1.  **No Implicit Calls**: You cannot say `say @x`. You must use parentheses: `say(@x)`.
2.  **Mandatory Blocks**: Single-line `if` statements are forbidden. Always use `{ }`.
    *   ❌ `if (@x > 0) say("Hi")`
    *   ✅ `if (@x > 0) { say("Hi") }`
3.  **Explicit Assignment**: You cannot just write `@x (10)`. You need the equals sign.
    *   ✅ `@x = (10)`
4.  **Variable Prefix**: Forgetting `@` on a user variable will cause a parse error.
    *   ❌ `name = ("John")`
    *   ✅ `@name = ("John")`

---

## 🧪 Complete Examples

### Example 1: Simple Greeting
```eplus
@user = input("Enter your name")

if (@user == "admin") {
    say("Welcome Admin")
} else {
    say("Hello ")
    say(@user)
}
```

### Example 2: Countdown Loop
```eplus
@count = (5)

repeat while (@count > 0) {
    say(@count)
    @count = (@count - 1)
}

say("Liftoff!")
```

### Example 3: Custom Function
```eplus
function CalculateArea(@width, @height) {
    @area = (@width * @height)
    return(@area)
}

@w = (10)
@h = (20)
@result = call CalculateArea(@w, @h)

say("The area is:")
say(@result)
```

---

## 🔍 Troubleshooting

| Error | Likely Cause | Fix |
| :--- | :--- | :--- |
| `Parse Error: Expected '('` | Missing parentheses around value | Change `@x = 10` to `@x = (10)` |
| `Parse Error: Expected '{'` | Missing block braces | Add `{ }` around your `if` or `loop` body |
| `Undefined Variable` | Missing `@` prefix | Ensure variable is written as `@name` |
| `Signal Generation Failed` | Invalid nesting | Check that all `{ }` are properly closed |

---

## 🚀 How to Run

1.  Save your code in a file ending with `.eplus` (e.g., `script.eplus`).
2.  Run the compiler:
    ```bash
    python main.py script.eplus
    ```
3.  The system will:
    *   Parse your E+ code.
    *   Generate Signal IR.
    *   Execute via Python.
    *   Save logs to `logs/execution_log.jsonl`.
