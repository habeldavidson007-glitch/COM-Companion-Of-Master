"""
JavaScript Expert Module for COM
Specialized in JavaScript/TypeScript development, ES6+ features, async programming, and best practices.
"""

import re
from typing import Dict, List, Any, Optional
from tools.base import BaseTool


class JavaScriptExpertTool(BaseTool):
    """Tool for JavaScript/TypeScript development assistance."""
    
    def __init__(self):
        super().__init__()
        self.name = "JavaScriptExpertTool"
        self.description = "Expert in JavaScript/TypeScript: ES6+, async/await, DOM manipulation, Node.js, frameworks, and modern best practices."
        self.js_versions = ["ES5", "ES6/ES2015", "ES2016", "ES2017", "ES2018", "ES2019", "ES2020", "ES2021", "ES2022", "ES2023"]
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute JavaScript-related tasks.
        
        Actions:
        - 'analyze_code': Analyze JS code for issues
        - 'modernize': Suggest ES6+ improvements
        - 'explain_concept': Explain JS concepts
        - 'generate_template': Generate JS code templates
        - 'check_async': Check async/await usage
        - 'convert_to_ts': Suggest TypeScript conversions
        """
        if action == "analyze_code":
            return self.analyze_code(kwargs.get("code", ""))
        elif action == "modernize":
            return self.modernize_code(kwargs.get("code", ""))
        elif action == "explain_concept":
            return self.explain_concept(kwargs.get("concept", ""))
        elif action == "generate_template":
            return self.generate_template(kwargs.get("template_type", "function"))
        elif action == "check_async":
            return self.check_async_usage(kwargs.get("code", ""))
        elif action == "convert_to_ts":
            return self.convert_to_typescript(kwargs.get("code", ""))
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "analyze_code", "modernize", "explain_concept",
                "generate_template", "check_async", "convert_to_ts"
            ]}
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code for issues and best practices."""
        issues = []
        suggestions = []
        strengths = []
        
        # Check for var usage
        if re.search(r'\bvar\s+\w+', code):
            suggestions.append("Replace 'var' with 'let' or 'const' for block scoping")
        
        # Check for const vs let
        has_const = bool(re.search(r'\bconst\s+\w+', code))
        has_let = bool(re.search(r'\blet\s+\w+', code))
        if has_const or has_let:
            strengths.append("Uses modern variable declarations (const/let)")
        
        # Check for == vs ===
        if re.search(r'[^=!]==[^=]', code) or re.search(r'[^!]==[^=]', code):
            suggestions.append("Use '===' instead of '==' for strict equality comparison")
        
        # Check for !important overuse
        if code.count('!important') > 3:
            suggestions.append("Excessive use of '!important' detected - consider refactoring CSS specificity")
        
        # Check for console.log in production
        if re.search(r'console\.(log|warn|error|debug)\s*\(', code):
            suggestions.append("Remove console statements before production deployment")
        
        # Check for arrow functions
        has_arrow = bool(re.search(r'=>', code))
        if has_arrow:
            strengths.append("Uses arrow functions for concise syntax")
        else:
            if re.search(r'function\s*\([^)]*\)\s*{', code):
                suggestions.append("Consider using arrow functions for shorter callbacks")
        
        # Check for template literals
        has_template = bool(re.search(r'`[^`]*\$\{', code))
        if has_template:
            strengths.append("Uses template literals for string interpolation")
        else:
            if re.search(r"['\"].*\+.*['\"]", code):
                suggestions.append("Consider using template literals instead of string concatenation")
        
        # Check for destructuring
        has_destructuring = bool(re.search(r'const\s*\{[^}]+\}\s*=', code) or 
                                re.search(r'const\s*\[[^\]]+\]\s*=', code))
        if has_destructuring:
            strengths.append("Uses destructuring assignment")
        else:
            if re.search(r'\.\w+\s*;', code):
                suggestions.append("Consider using destructuring for cleaner property access")
        
        # Check for Promise usage
        has_promise = bool(re.search(r'\bPromise\b|\.then\s*\(|\.catch\s*\(', code))
        has_async_await = bool(re.search(r'\basync\b|\bawait\b', code))
        if has_async_await:
            strengths.append("Uses async/await for asynchronous code")
        elif has_promise:
            suggestions.append("Consider using async/await instead of .then() chains")
        
        # Check for optional chaining
        has_optional_chaining = bool(re.search(r'\?\.', code))
        if has_optional_chaining:
            strengths.append("Uses optional chaining for safe property access")
        else:
            if re.search(r'&&\s*\w+\.\w+', code):
                suggestions.append("Consider using optional chaining (?.) instead of && checks")
        
        # Check for nullish coalescing
        has_nullish = bool(re.search(r'\?\?', code))
        if has_nullish:
            strengths.append("Uses nullish coalescing operator")
        else:
            if re.search(r'\|\|', code):
                suggestions.append("Consider using nullish coalescing (??) for null/undefined checks")
        
        # Check for module imports
        has_es6_import = bool(re.search(r'import\s+.*\s+from\s+["\']', code))
        has_require = bool(re.search(r'require\s*\(', code))
        if has_es6_import:
            strengths.append("Uses ES6 module imports")
        elif has_require:
            suggestions.append("Consider using ES6 imports instead of CommonJS require()")
        
        # Check for array methods
        array_methods = ['map', 'filter', 'reduce', 'find', 'some', 'every', 'includes']
        used_methods = [m for m in array_methods if re.search(rf'\.{m}\s*\(', code)]
        if used_methods:
            strengths.append(f"Uses functional array methods: {', '.join(used_methods)}")
        
        # Check for spread operator
        has_spread = bool(re.search(r'\.\.\.', code))
        if has_spread:
            strengths.append("Uses spread/rest operator")
        
        # Check for default parameters
        has_default_params = bool(re.search(r'function\s*\([^)]*=\s*[^)]*\)', code) or
                                 re.search(r'\([^)]*=\s*[^)]*\)\s*=>', code))
        if has_default_params:
            strengths.append("Uses default parameter values")
        else:
            if re.search(r'if\s*\([^)]*===?\s*(undefined|null)', code):
                suggestions.append("Consider using default parameters instead of undefined checks")
        
        return {
            "status": "analyzed",
            "issues": issues,
            "suggestions": suggestions,
            "strengths": strengths,
            "features_detected": {
                "arrow_functions": has_arrow,
                "template_literals": has_template,
                "destructuring": has_destructuring,
                "async_await": has_async_await,
                "optional_chaining": has_optional_chaining,
                "nullish_coalescing": has_nullish,
                "es6_modules": has_es6_import,
                "spread_operator": has_spread,
                "default_parameters": has_default_params
            }
        }
    
    def modernize_code(self, code: str) -> Dict[str, Any]:
        """Suggest modern JavaScript improvements for legacy code."""
        suggestions = []
        
        # var to const/let
        var_matches = re.findall(r'var\s+(\w+)\s*=\s*([^;]+);', code)
        for var_name, var_value in var_matches[:5]:
            keyword = 'const' if 'function' not in var_value and '=' not in var_value else 'let'
            suggestions.append({
                "before": f"var {var_name} = {var_value};",
                "after": f"{keyword} {var_name} = {var_value};",
                "benefit": "Block scoping prevents hoisting issues"
            })
        
        # String concatenation to template literals
        concat_matches = re.findall(r'["\']([^"\']*)["\']\s*\+\s*(\w+)\s*\+\s*["\']([^"\']*)["\']', code)
        for match in concat_matches[:3]:
            suggestions.append({
                "before": f"'{match[0]}' + {match[1]} + '{match[2]}'",
                "after": f"`{match[0]}${{{match[1]}}}{match[2]}`",
                "benefit": "Cleaner string interpolation"
            })
        
        # Function expressions to arrow functions
        func_matches = re.findall(r'function\s*\(([^)]*)\)\s*{\s*return\s+([^;]+);?\s*}', code)
        for params, body in func_matches[:3]:
            suggestions.append({
                "before": f"function({params}) {{ return {body}; }}",
                "after": f"({params}) => {body}",
                "benefit": "More concise syntax, lexical 'this'"
            })
        
        # .then() to async/await
        if re.search(r'\.then\s*\(', code):
            suggestions.append({
                "before": "fetch(url).then(res => res.json()).then(data => ...)",
                "after": "const res = await fetch(url); const data = await res.json();",
                "benefit": "Flatter, more readable async code"
            })
        
        # Object property shorthand
        if re.search(r'(\w+)\s*:\s*\1\s*[,\}]', code):
            suggestions.append({
                "before": "{ name: name, age: age }",
                "after": "{ name, age }",
                "benefit": "Cleaner object literal syntax"
            })
        
        return {
            "modernization_suggestions": suggestions,
            "target_standard": "ES2022+",
            "note": "Apply changes incrementally and test thoroughly"
        }
    
    def explain_concept(self, concept: str) -> str:
        """Explain JavaScript programming concepts."""
        concept_lower = concept.lower()
        
        explanations = {
            "closure": """
Closures in JavaScript:
=======================
A closure is a function that remembers its outer variables even when called outside its original scope.

Example:
function createCounter() {
    let count = 0;
    return function() {
        count++;
        return count;
    };
}

const counter = createCounter();
console.log(counter()); // 1
console.log(counter()); // 2

Key Points:
- Inner function has access to outer function's variables
- Variables persist between function calls
- Commonly used for data privacy and function factories
""",
            "promise": """
Promises in JavaScript:
=======================
A Promise represents the eventual completion (or failure) of an asynchronous operation.

States:
- Pending: Initial state
- Fulfilled: Operation completed successfully
- Rejected: Operation failed

Example:
const promise = new Promise((resolve, reject) => {
    setTimeout(() => {
        resolve("Success!");
    }, 1000);
});

promise
    .then(result => console.log(result))
    .catch(error => console.error(error));

Async/Await (syntactic sugar over Promises):
async function fetchData() {
    try {
        const result = await promise;
        console.log(result);
    } catch (error) {
        console.error(error);
    }
}
""",
            "arrow_function": """
Arrow Functions in JavaScript:
==============================
Concise syntax for writing function expressions.

Syntax:
// Basic
const add = (a, b) => a + b;

// With block
const multiply = (a, b) => {
    return a * b;
};

// Single parameter (parentheses optional)
const square = x => x * x;

// No parameters
const greet = () => "Hello!";

Key Differences from Regular Functions:
1. Lexical 'this' - inherits from surrounding context
2. Cannot be used as constructors (no 'new')
3. No 'arguments' object
4. More concise syntax

Good for:
- Callbacks
- Array methods (map, filter, reduce)
- Short utility functions
""",
            "destructuring": """
Destructuring in JavaScript:
============================
Extract values from arrays or objects into distinct variables.

Object Destructuring:
const person = { name: 'John', age: 30, city: 'NYC' };
const { name, age } = person;
console.log(name); // 'John'

With renaming:
const { name: fullName, age } = person;

Array Destructuring:
const colors = ['red', 'green', 'blue'];
const [first, second] = colors;
console.log(first); // 'red'

Skip elements:
const [, , third] = colors;

Default values:
const { name, country = 'USA' } = person;

Nested destructuring:
const user = {
    profile: { firstName: 'John', lastName: 'Doe' }
};
const { profile: { firstName } } = user;
""",
            "spread_rest": """
Spread and Rest Operators:
==========================
The ... syntax serves two purposes:

Spread Operator (expands):
// Array
const arr1 = [1, 2, 3];
const arr2 = [...arr1, 4, 5]; // [1, 2, 3, 4, 5]

// Object
const obj1 = { a: 1, b: 2 };
const obj2 = { ...obj1, c: 3 }; // { a: 1, b: 2, c: 3 }

// Function call
const nums = [1, 5, 3];
Math.max(...nums); // 5

Rest Operator (collects):
// Function parameters
function sum(...numbers) {
    return numbers.reduce((a, b) => a + b, 0);
}
sum(1, 2, 3); // 6

// Array destructuring
const [first, ...rest] = [1, 2, 3, 4];
// first = 1, rest = [2, 3, 4]

// Object destructuring
const { a, ...others } = { a: 1, b: 2, c: 3 };
// a = 1, others = { b: 2, c: 3 }
""",
            "async_await": """
Async/Await in JavaScript:
==========================
Syntactic sugar over Promises for writing asynchronous code.

Basic Syntax:
async function fetchData() {
    try {
        const response = await fetch('https://api.example.com/data');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

Key Points:
- 'async' keyword makes a function return a Promise
- 'await' pauses execution until Promise resolves
- Can only use 'await' inside 'async' functions
- Use try/catch for error handling

Parallel Execution:
// Sequential (slower)
const user = await fetchUser();
const posts = await fetchPosts(user.id);

// Parallel (faster)
const [user, posts] = await Promise.all([
    fetchUser(),
    fetchPosts(userId)
]);
""",
            "modules": """
JavaScript Modules (ES6):
=========================
Modules allow code organization across multiple files.

Named Exports:
// math.js
export const PI = 3.14159;
export function add(a, b) {
    return a + b;
}

// Import named exports
import { PI, add } from './math.js';

Default Export:
// utils.js
export default function formatDate(date) {
    return date.toISOString();
}

// Import default export
import formatDate from './utils.js';

Re-export:
export { PI, add } from './math.js';
export * from './math.js';

Dynamic Import:
const module = await import('./dynamic-module.js');
module.someFunction();

CommonJS (Node.js legacy):
const module = require('./module.js');
module.exports = { ... };
""",
            "optional_chaining": """
Optional Chaining (?.):
=======================
Safely access nested properties without checking each level.

Traditional approach:
const street = user && user.address && user.address.street;

With optional chaining:
const street = user?.address?.street;

Works with:
// Property access
const value = obj?.property;

// Method calls
const result = obj?.method?.();

// Array access
const item = array?.[index];

Nullish Coalescing (??):
// Provide default for null/undefined only
const name = user?.name ?? 'Anonymous';
// Different from || which also treats 0, false, '' as falsy
"""
        }
        
        for key, explanation in explanations.items():
            if key.replace('_', ' ') in concept_lower or key in concept_lower:
                return explanation
        
        return f"Concept '{concept}' not found. Try: closure, promise, arrow_function, destructuring, spread_rest, async_await, modules, optional_chaining"
    
    def generate_template(self, template_type: str) -> str:
        """Generate JavaScript code templates."""
        templates = {
            "function": '''// Modern JavaScript Function Template
/**
 * Description of the function
 * @param {type} paramName - Description
 * @returns {type} Description
 */
const functionName = (param1, param2 = defaultValue) => {
    // Implementation
    return result;
};

// Export for modules
export { functionName };
''',
            "class": '''// ES6 Class Template
class ClassName {
    constructor(initialValue) {
        this._value = initialValue;
        this._listeners = [];
    }
    
    // Getter
    get value() {
        return this._value;
    }
    
    // Setter
    set value(newValue) {
        if (newValue !== this._value) {
            this._value = newValue;
            this._notifyListeners();
        }
    }
    
    // Public method
    doSomething(param) {
        // Implementation
        return this; // For chaining
    }
    
    // Private method (using #)
    #privateMethod() {
        // Internal logic
    }
    
    // Static method
    static createDefault() {
        return new ClassName();
    }
    
    _notifyListeners() {
        this._listeners.forEach(cb => cb(this._value));
    }
}

export { ClassName };
''',
            "react_component": '''// React Functional Component Template (with Hooks)
import React, { useState, useEffect, useCallback, useMemo } from 'react';

const ComponentName = ({ initialData, onAction }) => {
    // State
    const [data, setData] = useState(initialData);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // Memoized value
    const processedData = useMemo(() => {
        return data.map(item => /* transform */);
    }, [data]);
    
    // Callback
    const handleAction = useCallback(async (param) => {
        setLoading(true);
        try {
            const result = await someAsyncOperation(param);
            setData(result);
            onAction?.(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [onAction]);
    
    // Effect
    useEffect(() => {
        // Setup
        const subscription = subscribeToSomething();
        
        // Cleanup
        return () => subscription.unsubscribe();
    }, []);
    
    // Render
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    
    return (
        <div className="component-name">
            {/* JSX content */}
        </div>
    );
};

export default ComponentName;
''',
            "express_route": '''// Express.js Route Template
import express from 'express';
import { validationResult } from 'express-validator';

const router = express.Router();

/**
 * GET /resource
 * Retrieve list of resources
 */
router.get('/', async (req, res, next) => {
    try {
        const { page = 1, limit = 10, sort = 'createdAt' } = req.query;
        
        const resources = await Resource.find()
            .limit(limit * 1)
            .skip((page - 1) * limit)
            .sort({ [sort]: -1 });
        
        const count = await Resource.countDocuments();
        
        res.json({
            data: resources,
            pagination: {
                total: count,
                page: parseInt(page),
                pages: Math.ceil(count / limit)
            }
        });
    } catch (error) {
        next(error);
    }
});

/**
 * POST /resource
 * Create new resource
 */
router.post('/', validationMiddleware, async (req, res, next) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }
        
        const resource = await Resource.create(req.body);
        res.status(201).json({ data: resource });
    } catch (error) {
        next(error);
    }
});

export default router;
''',
            "test_jest": '''// Jest Test Template
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { functionName } from '../source';

describe('FunctionName', () => {
    // Mock dependencies
    const mockDependency = jest.fn();
    
    beforeEach(() => {
        jest.clearAllMocks();
    });
    
    describe('success cases', () => {
        it('should return expected value', () => {
            const result = functionName('input');
            expect(result).toBe('expected');
        });
        
        it('should handle edge case', () => {
            const result = functionName('');
            expect(result).toBeDefined();
        });
    });
    
    describe('error cases', () => {
        it('should throw error for invalid input', () => {
            expect(() => functionName(null)).toThrow();
        });
    });
    
    describe('async operations', () => {
        it('should resolve with correct data', async () => {
            mockDependency.mockResolvedValue({ id: 1 });
            const result = await functionName('input');
            expect(result).toHaveProperty('id');
        });
    });
});
'''
        }
        
        return templates.get(template_type, f"Template '{template_type}' not found. Available: function, class, react_component, express_route, test_jest")
    
    def check_async_usage(self, code: str) -> Dict[str, Any]:
        """Check async/await usage patterns in code."""
        analysis = {
            "has_async": bool(re.search(r'\basync\b', code)),
            "has_await": bool(re.search(r'\bawait\b', code)),
            "has_promise_chains": bool(re.search(r'\.then\s*\(', code)),
            "has_callback_hell": False,
            "issues": [],
            "suggestions": []
        }
        
        # Check for callback hell (nested callbacks)
        nesting_depth = 0
        max_nesting = 0
        for char in code:
            if char == '{':
                nesting_depth += 1
                max_nesting = max(max_nesting, nesting_depth)
            elif char == '}':
                nesting_depth -= 1
        
        if max_nesting > 4:
            analysis["has_callback_hell"] = True
            analysis["issues"].append(f"Deep nesting detected ({max_nesting} levels) - consider async/await")
        
        # Check for unhandled promises
        if analysis["has_async"] and not re.search(r'\btry\b', code):
            analysis["issues"].append("Async function without try/catch - potential unhandled rejection")
        
        # Check for await in loops (can be parallelized)
        if re.search(r'for\s*\([^)]*\)\s*{\s*await', code):
            analysis["suggestions"].append("Consider using Promise.all() for parallel execution in loops")
        
        # Check for missing await
        if re.search(r'(?:const|let|var)\s+\w+\s*=\s*\w+\([^)]*\)', code) and analysis["has_async"]:
            if not re.search(r'await\s+\w+\(', code):
                analysis["suggestions"].append("Possible missing 'await' keyword")
        
        return analysis
    
    def convert_to_typescript(self, code: str) -> Dict[str, Any]:
        """Suggest TypeScript conversions for JavaScript code."""
        suggestions = []
        
        # Detect variable declarations
        var_patterns = [
            (r'const\s+(\w+)\s*=\s*(\d+)', r'const \1: number = \2'),
            (r'const\s+(\w+)\s*=\s*"([^"]*)"', r'const \1: string = "\2"'),
            (r'const\s+(\w+)\s*=\s*true', r'const \1: boolean = true'),
            (r'const\s+(\w+)\s*=\s*\[\]', r'const \1: any[] = []'),
            (r'const\s+(\w+)\s*=\s*\{\}', r'const \1: Record<string, any> = {}'),
        ]
        
        for pattern, replacement in var_patterns:
            matches = re.findall(pattern, code)
            if matches:
                examples = [f"{m[0]}: {type(m[1]).__name__}" for m in matches[:3]]
                suggestions.append({
                    "category": "type_annotations",
                    "message": f"Add type annotations: {', '.join(examples)}"
                })
        
        # Detect function parameters
        if re.search(r'function\s+\w+\s*\([^)]+\)', code):
            suggestions.append({
                "category": "function_types",
                "message": "Add parameter types: function name(param: type): returnType"
            })
        
        # Detect arrow functions
        if re.search(r'\([^)]*\)\s*=>', code):
            suggestions.append({
                "category": "arrow_function_types",
                "message": "Add types: (param: type): ReturnType => {}"
            })
        
        # Detect object literals
        if re.search(r'\{\s*\w+\s*:', code):
            suggestions.append({
                "category": "interface",
                "message": "Consider creating interfaces for object types"
            })
        
        return {
            "typescript_suggestions": suggestions,
            "next_steps": [
                "Install TypeScript: npm install -D typescript",
                "Create tsconfig.json: npx tsc --init",
                "Rename .js files to .ts or .tsx",
                "Fix type errors incrementally"
            ]
        }
