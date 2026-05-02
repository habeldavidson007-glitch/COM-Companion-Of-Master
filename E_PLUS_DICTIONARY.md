# E+ Language — 10 Minute Learning Model

## Goal

Teach complete beginners the core of E+ in under 10 minutes while preserving full power.

---

## 1. Mental Model (1 minute)

E+ is based on 3 ideas:

1. **You create things** → `@name`
2. **You do actions** → `say()`, `input()`
3. **You control flow** → `if`, `repeat`

Think of it as:

> "Tell the system what you want, step by step"

---

## 🧠 VISUAL MODEL (Flow → Block → Signal)

**Human Intent:**
"Ask name → greet user"

↓

**E+ Code:**
```e+
@name = input("Name?")
say("Hello " + @name)
```

↓

**Signal (Internal):**
```
INPUT → ASSIGN → OUTPUT
```

↓

**Execution (Python):**
```python
name = input("Name?")
print("Hello " + name)
```

👉 **E+** = readable layer  
👉 **Signal** = execution brain

---

## 2. Variables (1 minute)

```e+
@name = ("John")
```

* `@` means "this is something I created"
* `( )` holds data

---

## 3. Input & Output (2 minutes)

```e+
@name = input("What is your name?")
say("Hello " + @name)
```

* `input()` = ask user
* `say()` = show output

---

## 4. Condition (2 minutes)

```e+
if (@age > 18) {
    say("Adult")
} else {
    say("Minor")
}
```

* `if` = check something
* `{ }` = block of actions

---

## 5. Loop (2 minutes)

```e+
repeat (@i, 5) {
    say(@i)
}
```

* repeat something multiple times

---

## 6. Function (1 minute)

```e+
function greet(@name) {
    say("Hello " + @name)
}

call greet("David")
```

* `function` = reusable action
* `call` = run it

---

## 🚀 MINI PROJECT (15 Minutes)

### Goal: Simple Login System

**Step 1 — Ask user name**
```e+
@name = input("Enter your name")
```

**Step 2 — Ask age**
```e+
@age = input("Enter your age")
```

**Step 3 — Add condition**
```e+
if (@age > 17) {
    say("Access granted")
} else {
    say("Access denied")
}
```

**Step 4 — Personalize response**
```e+
say("Hello " + @name)
```

---

### Final Program

```e+
@name = input("Enter your name")
@age = input("Enter your age")

if (@age > 17) {
    say("Access granted")
} else {
    say("Access denied")
}

say("Hello " + @name)
```

---

## 🧠 What You Just Learned

* Variables
* Input / Output
* Conditions
* Program flow

👉 This is already enough to build real programs.

---

## 7. Rules to Remember (30 sec)

* Always use `@` for variables
* Always use `( )` for values
* Always use `{ }` for blocks
* Use clear words: `say`, `input`, `repeat`

---

## 8. Why It Works

* Same structure everywhere
* No hidden syntax
* Reads like instructions

---

## ❌ Common Mistakes (Debug Mindset)

### 1. Forgetting `@`

```e+
name = ("John")   ❌
@name = ("John")  ✅
```
👉 Always mark your variables.

---

### 2. Missing parentheses

```e+
say "Hello"   ❌
say("Hello")  ✅
```
👉 Actions always use `( )`

---

### 3. Missing block `{ }`

```e+
if (@x > 0) say("Hi") ❌
if (@x > 0) { say("Hi") } ✅
```
👉 Blocks are never optional.

---

### 4. Treating E+ like Python

```e+
print("Hello") ❌
say("Hello")   ✅
```
👉 Use E+ intent, not Python syntax.

---

## 🧠 How E+ Thinks vs Python Thinks

### Python Thinking
* How do I write this correctly?
* Where do I put `:`?
* Indentation matters

Example:
```python
if x > 0:
    print("Hi")
```

---

### E+ Thinking
* What do I want to happen?
* What is the condition?
* What should the system do?

Example:
```e+
if (@x > 0) {
    say("Hi")
}
```

---

### Key Difference

**Python:** "Write correct syntax"  
**E+:** "Express clear intent"

---

## 🧭 Final Thought

E+ is not about writing less.  
It is about thinking less while staying powerful.

And once you understand the intent,  
E+ becomes predictable, readable, and scalable.

---

# 📖 Complete Symbol & Keyword Dictionary

## 🔣 Symbols

| Symbol | Name | Usage | Example |
|--------|------|-------|---------|
| `@` | Entity Marker | Prefix for all variables | `@name` |
| `( )` | Data Container | Wraps values and expressions | `("Hello")`, `(@a + @b)` |
| `{ }` | Block Delimiter | Groups statements in control flow | `if (...) { ... }` |
| `=` | Assignment | Assigns value to variable | `@x = (10)` |
| `+ - * /` | Math Operators | Arithmetic operations | `(@a + @b)` |
| `> < == !=` | Comparators | Conditional checks | `if (@x > 5)` |
| `"` | String Delimiter | Defines text literals | `"Hello World"` |

---

## 🔑 Keywords Reference

### Core Actions

| Keyword | Purpose | Syntax | Example |
|---------|---------|--------|---------|
| `input` | Request user input | `@var = input("prompt")` | `@name = input("Name?")` |
| `say` | Display output | `say(expression)` | `say("Hello")` |
| `return` | Return from function | `return(expression)` | `return(@result)` |

### Control Flow

| Keyword | Purpose | Syntax | Example |
|---------|---------|--------|---------|
| `if` | Conditional branch | `if (cond) { ... }` | `if (@x > 0) { ... }` |
| `else if` | Alternative condition | `else if (cond) { ... }` | `else if (@x < 0) { ... }` |
| `else` | Default branch | `else { ... }` | `else { say("Default") }` |
| `repeat` | Loop (range or while) | `repeat (var, count) { ... }`<br>`repeat while (cond) { ... }` | `repeat (@i, 5) { ... }` |
| `break` | Exit loop | `break` | `if (@x > 10) { break }` |
| `exit` | Terminate program | `exit` | `if (@error) { exit }` |

### Functions

| Keyword | Purpose | Syntax | Example |
|---------|---------|--------|---------|
| `function` | Define reusable block | `function Name(@args) { ... }` | `function Add(@a, @b) { ... }` |
| `call` | Invoke function | `call Name(args)` | `call Add(10, 20)` |

---

## 🔄 Signal Mapping Reference

Every E+ construct maps 1:1 to a Signal IR type:

| E+ Construct | Signal Type | Description |
|--------------|-------------|-------------|
| `@x = (...)` | `ASSIGN` | Variable assignment |
| `input(...)` | `INPUT` | User input request |
| `say(...)` | `OUTPUT` | Display output |
| `if (...) { }` | `IF` | Conditional branch |
| `repeat (...) { }` | `LOOP` | Iteration |
| `function ...` | `FUNCTION_DEF` | Function definition |
| `call ...` | `CALL` | Function invocation |
| `return(...)` | `RETURN` | Function return |
| `break` | `BREAK` | Loop termination |
| `exit` | `EXIT` | Program termination |

---

## 📝 Grammar Rules (Strict)

1. **Variables must start with `@`**
   - ✅ `@name`
   - ❌ `name`

2. **All values must be in parentheses**
   - ✅ `@x = (10)`
   - ❌ `@x = 10`

3. **All actions require parentheses**
   - ✅ `say("Hello")`
   - ❌ `say "Hello"`

4. **Blocks are mandatory for control flow**
   - ✅ `if (@x > 0) { say("Hi") }`
   - ❌ `if (@x > 0) say("Hi")`

5. **No implicit behavior**
   - Every operation must be explicit
   - No automatic type coercion

---

## 🧪 Complete Examples

### Example 1: Greeting Program

```e+
@name = input("What is your name?")
say("Hello " + @name)
```

**Signal:**
```json
[
  {"type": "INPUT", "target": "name", "prompt": "What is your name?"},
  {"type": "OUTPUT", "content": {"op": "+", "left": "Hello ", "right": "@name"}}
]
```

---

### Example 2: Age Checker

```e+
@age = input("Enter your age")

if (@age > 17) {
    say("Access granted")
} else {
    say("Access denied")
}
```

**Signal:**
```json
[
  {"type": "INPUT", "target": "age", "prompt": "Enter your age"},
  {
    "type": "IF",
    "condition": {"op": ">", "left": "@age", "right": 17},
    "then": [{"type": "OUTPUT", "content": "Access granted"}],
    "else": [{"type": "OUTPUT", "content": "Access denied"}]
  }
]
```

---

### Example 3: Counter Loop

```e+
repeat (@i, 5) {
    say("Count: " + @i)
}
```

**Signal:**
```json
[
  {
    "type": "LOOP",
    "kind": "range",
    "variable": "i",
    "count": 5,
    "body": [
      {"type": "OUTPUT", "content": {"op": "+", "left": "Count: ", "right": "@i"}}
    ]
  }
]
```

---

### Example 4: Function Definition & Call

```e+
function Add(@a, @b) {
    @result = (@a + @b)
    return(@result)
}

@sum = call Add(10, 20)
say("Sum: " + @sum)
```

**Signal:**
```json
[
  {
    "type": "FUNCTION_DEF",
    "name": "Add",
    "params": ["a", "b"],
    "body": [
      {"type": "ASSIGN", "target": "result", "value": {"op": "+", "left": "@a", "right": "@b"}},
      {"type": "RETURN", "value": "@result"}
    ]
  },
  {"type": "CALL", "function": "Add", "args": [10, 20], "target": "sum"},
  {"type": "OUTPUT", "content": {"op": "+", "left": "Sum: ", "right": "@sum"}}
]
```

---

## 🔍 Troubleshooting Guide

| Error | Cause | Fix |
|-------|-------|-----|
| `Expected '@'` | Variable missing `@` prefix | Add `@` before variable name |
| `Expected '('` | Missing parentheses around value | Wrap value in `( )` |
| `Expected '{'` | Missing block delimiter | Add `{ }` around block |
| `Unknown keyword` | Typo or invalid keyword | Check spelling against dictionary |
| `Unmatched ')'` | Missing opening parenthesis | Ensure all `( )` are paired |
| `Unmatched '}'` | Missing opening brace | Ensure all `{ }` are paired |

---

## 📚 Next Steps

Once you master these basics:

1. **Practice**: Build small programs using the mini-project template
2. **Explore**: Try nested conditions and loops
3. **Extend**: Create reusable functions for common tasks
4. **Debug**: Use the structured logs to understand execution flow

Remember: **Clarity over brevity. Intent over syntax.**
