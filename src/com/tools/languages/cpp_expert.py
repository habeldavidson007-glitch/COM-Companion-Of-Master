"""
C++ Expert Module for COM
Specialized in C++ development, memory management, modern C++ features, and best practices.
"""

import re
from typing import Dict, List, Any, Optional
from tools.base import BaseTool

class CppExpertTool(BaseTool):
    """Tool for C++ development assistance."""
    
    def __init__(self):
        super().__init__()
        self.name = "CppExpertTool"
        self.description = "Expert in C++ development: memory management, smart pointers, STL, CMake, modern C++ (11/14/17/20), and performance optimization."
        self.cpp_versions = ["C++98", "C++11", "C++14", "C++17", "C++20", "C++23"]
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute C++-related tasks.
        
        Actions:
        - 'analyze_code': Analyze C++ code for issues
        - 'suggest_modernization': Suggest modern C++ improvements
        - 'explain_concept': Explain C++ concepts
        - 'generate_template': Generate C++ code templates
        - 'check_memory_safety': Check for memory safety issues
        """
        if action == "analyze_code":
            return self.analyze_code(kwargs.get("code", ""))
        elif action == "suggest_modernization":
            return self.suggest_modernization(kwargs.get("code", ""))
        elif action == "explain_concept":
            return self.explain_concept(kwargs.get("concept", ""))
        elif action == "generate_template":
            return self.generate_template(kwargs.get("template_type", "class"))
        elif action == "check_memory_safety":
            return self.check_memory_safety(kwargs.get("code", ""))
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "analyze_code", "suggest_modernization", "explain_concept",
                "generate_template", "check_memory_safety"
            ]}
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze C++ code for issues and best practices."""
        issues = []
        suggestions = []
        strengths = []
        
        # Check for raw new/delete
        if re.search(r'\bnew\b', code):
            if not re.search(r'(unique_ptr|shared_ptr|make_unique|make_shared)', code):
                issues.append("Raw 'new' detected. Consider using smart pointers (unique_ptr, shared_ptr)")
        
        if re.search(r'\bdelete\b', code):
            issues.append("Raw 'delete' detected. Use smart pointers for automatic memory management")
        
        # Check for C-style casts
        if re.search(r'\(int\)|\(float\)|\(double\)|\(char\*\)|\(void\*\)', code):
            suggestions.append("Replace C-style casts with static_cast, dynamic_cast, or reinterpret_cast")
        
        # Check for NULL vs nullptr
        if re.search(r'\bNULL\b', code):
            suggestions.append("Use 'nullptr' instead of 'NULL' (C++11 and later)")
        
        # Check for auto keyword usage
        has_auto = bool(re.search(r'\bauto\b', code))
        if not has_auto and len(code.split()) > 50:
            suggestions.append("Consider using 'auto' for complex type declarations")
        elif has_auto:
            strengths.append("Uses 'auto' for cleaner code")
        
        # Check for range-based for loops
        if re.search(r'for\s*\(\s*int\s+\w+\s*=', code):
            suggestions.append("Consider using range-based for loops where applicable")
        
        # Check for override keyword
        if re.search(r'virtual\s+.*\s*=\s*0', code) or re.search(r'virtual\s+\w+', code):
            if 'override' not in code:
                suggestions.append("Add 'override' keyword to overriding virtual functions")
        
        # Check for const correctness
        if re.search(r'void\s+\w+\s*\([^)]*\)\s*(const)?\s*{', code):
            if 'const' not in code:
                suggestions.append("Consider 'const' correctness for member functions that don't modify state")
        
        # Check for move semantics
        if re.search(r'const\s+\w+\s*&', code):
            if '&&' not in code:
                suggestions.append("Consider implementing move constructor/assignment for efficiency")
        
        # Check for std:: prefix
        missing_std = bool(re.search(r'\b(vector|string|map|set|cout|cin|unique_ptr|shared_ptr)\b', code))
        if missing_std and 'using namespace std' not in code:
            strengths.append("Properly uses std:: namespace or explicit imports")
        elif 'using namespace std' in code:
            suggestions.append("Avoid 'using namespace std;' in header files")
        
        return {
            "status": "analyzed",
            "issues": issues,
            "suggestions": suggestions,
            "strengths": strengths,
            "cpp_features_detected": {
                "smart_pointers": bool(re.search(r'(unique_ptr|shared_ptr)', code)),
                "auto_keyword": has_auto,
                "range_based_for": bool(re.search(r'for\s*\(\s*auto', code)),
                "lambdas": bool(re.search(r'\[\]', code)),
                "move_semantics": bool(re.search(r'&&', code))
            }
        }
    
    def suggest_modernization(self, code: str) -> Dict[str, Any]:
        """Suggest modern C++ improvements for legacy code."""
        suggestions = []
        
        # Raw pointers to smart pointers
        if re.search(r'int\s*\*\s*\w+\s*=\s*new\s+int', code):
            suggestions.append({
                "before": "int* ptr = new int(5); delete ptr;",
                "after": "auto ptr = std::make_unique<int>(5);",
                "benefit": "Automatic memory management, no manual delete needed"
            })
        
        # C-style arrays to std::array or std::vector
        if re.search(r'int\s+\w+\s*\[\s*\d+\s*\]', code):
            suggestions.append({
                "before": "int arr[10];",
                "after": "std::array<int, 10> arr; or std::vector<int> arr(10);",
                "benefit": "Bounds checking, size tracking, STL algorithms"
            })
        
        # C-style strings to std::string
        if re.search(r'char\s*\*\s*\w+\s*=\s*"', code):
            suggestions.append({
                "before": 'char* str = "hello";',
                'after': 'std::string str = "hello";',
                "benefit": "Automatic memory management, string operations"
            })
        
        # Manual loops to STL algorithms
        if re.search(r'for\s*\([^)]*push_back', code):
            suggestions.append({
                "before": "for(...) { vec.push_back(val); }",
                "after": "std::transform(...) or use initializer list",
                "benefit": "More expressive, potentially optimized"
            })
        
        # printf/scanf to iostream or fmt
        if re.search(r'printf\s*\(|scanf\s*\(', code):
            suggestions.append({
                "before": 'printf("%d", value);',
                "after": 'std::cout << value; or fmt::print("{}", value);',
                "benefit": "Type safety, extensibility"
            })
        
        return {
            "modernization_suggestions": suggestions,
            "target_standard": "C++17/C++20",
            "note": "Apply changes incrementally and test thoroughly"
        }
    
    def explain_concept(self, concept: str) -> str:
        """Explain C++ programming concepts."""
        concept_lower = concept.lower()
        
        explanations = {
            "smart_pointer": """
Smart Pointers in C++:
Automatic memory management wrappers that prevent memory leaks.

Types:
1. unique_ptr: Exclusive ownership, cannot be copied
   std::unique_ptr<int> ptr = std::make_unique<int>(5);

2. shared_ptr: Shared ownership with reference counting
   std::shared_ptr<int> ptr = std::make_shared<int>(5);

3. weak_ptr: Non-owning reference to shared_ptr
   std::weak_ptr<int> weak = ptr;

Benefits:
- No manual delete required
- Exception safe
- Clear ownership semantics
""",
            "move_semantics": """
Move Semantics in C++11:
Efficiently transfer resources instead of copying.

Key Concepts:
- Rvalue references (&&)
- std::move() to cast to rvalue
- Move constructor and move assignment

Example:
class MyClass {
    std::vector<int> data;
public:
    // Move constructor
    MyClass(MyClass&& other) noexcept 
        : data(std::move(other.data)) {}
    
    // Move assignment
    MyClass& operator=(MyClass&& other) noexcept {
        data = std::move(other.data);
        return *this;
    }
};

Usage:
MyClass obj1;
MyClass obj2 = std::move(obj1);  // Transfers resources
""",
            "lambda": """
Lambda Expressions in C++:
Anonymous functions defined inline.

Syntax: [capture](parameters) -> return_type { body }

Examples:
// Simple lambda
auto add = [](int a, int b) { return a + b; };

// With capture by value
int x = 5;
auto func = [x](int y) { return x + y; };

// With capture by reference
auto funcRef = [&x](int y) { x += y; };

// Generic lambda (C++14)
auto generic = [](auto a, auto b) { return a + b; };

Usage with STL:
std::vector<int> nums = {1, 2, 3};
std::sort(nums.begin(), nums.end(), [](int a, int b) {
    return a > b;  // Descending order
});
""",
            "const_correctness": """
Const Correctness in C++:
Using 'const' to express immutability guarantees.

Types:
1. Const variable: const int x = 5;
2. Const pointer: int* const ptr (pointer constant)
3. Pointer to const: const int* ptr (data constant)
4. Const member function: void func() const { ... }
5. Const parameter: void func(const std::string& str)

Best Practices:
- Use const for parameters that shouldn't be modified
- Mark member functions as const if they don't modify state
- Prefer const references for read-only parameters
- Use constexpr for compile-time constants (C++11)

Example:
class Counter {
    int count = 0;
public:
    int getCount() const { return count; }  // Doesn't modify
    void increment() { count++; }           // Modifies state
};
""",
            "raii": """
RAII (Resource Acquisition Is Initialization):
C++ idiom for resource management.

Principle: Acquire resources in constructor, release in destructor.

Example:
class FileHandler {
    FILE* file;
public:
    FileHandler(const char* filename) {
        file = fopen(filename, "r");  // Acquire
    }
    ~FileHandler() {
        if (file) fclose(file);        // Release
    }
};

Usage:
void processFile() {
    FileHandler handler("data.txt");  // Automatically closed
    // ... use file ...
}  // Destructor called automatically

Modern C++: Smart pointers are RAII for dynamic memory
""",
            "template": """
Templates in C++:
Generic programming mechanism.

Function Template:
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

Class Template:
template<typename T>
class Stack {
    std::vector<T> elements;
public:
    void push(const T& item) { elements.push_back(item); }
    T pop() { T top = elements.back(); elements.pop_back(); return top; }
};

Template Specialization:
template<>
bool max<bool>(bool a, bool b) {
    // Special implementation for bool
}

C++17 Features:
- Class template argument deduction: Stack s{1, 2, 3};
- Fold expressions: (args + ...)
- if constexpr: Compile-time branching
"""
        }
        
        for key, explanation in explanations.items():
            if key.replace('_', ' ') in concept_lower or key in concept_lower:
                return explanation
        
        return f"Concept '{concept}' not found. Try: smart_pointer, move_semantics, lambda, const_correctness, raii, template"
    
    def generate_template(self, template_type: str) -> str:
        """Generate C++ code templates."""
        templates = {
            "class": '''#pragma once

#include <string>
#include <memory>

class ClassName {
public:
    // Constructors
    ClassName();
    explicit ClassName(int value);
    ClassName(const ClassName& other);            // Copy constructor
    ClassName(ClassName&& other) noexcept;         // Move constructor
    
    // Assignment operators
    ClassName& operator=(const ClassName& other);  // Copy assignment
    ClassName& operator=(ClassName&& other) noexcept;  // Move assignment
    
    // Destructor
    ~ClassName();
    
    // Member functions
    void doSomething();
    int getValue() const;
    
    // Static members
    static int getInstanceCount();
    
private:
    int value_;
    static int instanceCount_;
};

// Implementation example (.cpp)
/*
ClassName::ClassName() : value_(0) {
    instanceCount_++;
}

ClassName::~ClassName() {
    instanceCount_--;
}

int ClassName::getValue() const {
    return value_;
}
*/
''',
            "singleton": '''#pragma once

#include <memory>

class Singleton {
public:
    // Delete copy/move operations
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
    Singleton(Singleton&&) = delete;
    Singleton& operator=(Singleton&&) = delete;
    
    // Global access point
    static Singleton& getInstance() {
        static Singleton instance;  // Meyers' singleton (thread-safe in C++11)
        return instance;
    }
    
    void doWork();
    
private:
    Singleton() = default;
    ~Singleton() = default;
};
''',
            "cmake": '''cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Options
option(BUILD_TESTS "Build tests" ON)
option(USE_ASAN "Use Address Sanitizer" OFF)

# Source files
set(SOURCES
    src/main.cpp
    src/class1.cpp
    src/class2.cpp
)

set(HEADERS
    include/class1.hpp
    include/class2.hpp
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS})

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Compiler warnings
if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE /W4)
else()
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Sanitizers (optional)
if(USE_ASAN)
    target_compile_options(${PROJECT_NAME} PRIVATE -fsanitize=address)
    target_link_options(${PROJECT_NAME} PRIVATE -fsanitize=address)
endif()

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Installation
install(TARGETS ${PROJECT_NAME} DESTINATION bin)
''',
            "unittest": '''#include <gtest/gtest.h>
#include "your_class.hpp"

class YourClassTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup before each test
    }
    
    void TearDown() override {
        // Cleanup after each test
    }
};

TEST_F(YourClassTest, BasicFunctionality) {
    YourClass obj;
    EXPECT_EQ(obj.getValue(), 0);
}

TEST_F(YourClassTest, SetValue) {
    YourClass obj;
    obj.setValue(42);
    EXPECT_EQ(obj.getValue(), 42);
}

TEST(StandaloneTest, SimpleAssertion) {
    EXPECT_TRUE(true);
    ASSERT_EQ(2 + 2, 4);
}

// Parameterized test
class ParamTest : public ::testing::TestWithParam<int> {};

TEST_P(ParamTest, WithParameter) {
    int param = GetParam();
    EXPECT_GE(param, 0);
}

INSTANTIATE_TEST_SUITE_P(
    Instances,
    ParamTest,
    ::testing::Values(1, 2, 3, 4, 5)
);
'''
        }
        
        return templates.get(template_type, f"Template '{template_type}' not found. Available: class, singleton, cmake, unittest")
    
    def check_memory_safety(self, code: str) -> Dict[str, Any]:
        """Check C++ code for memory safety issues."""
        issues = []
        
        # Raw new without delete
        new_count = len(re.findall(r'\bnew\b', code))
        delete_count = len(re.findall(r'\bdelete\b', code))
        if new_count > delete_count:
            issues.append({
                "severity": "HIGH",
                "issue": f"Potential memory leak: {new_count} 'new' but only {delete_count} 'delete'",
                "recommendation": "Use smart pointers or ensure all allocations are freed"
            })
        
        # Array new with scalar delete
        if re.search(r'new\s+\w+\s*\[', code) and re.search(r'delete\s+(?!\[)', code):
            issues.append({
                "severity": "CRITICAL",
                "issue": "Mismatched new[]/delete: array allocated, scalar delete used",
                "recommendation": "Use delete[] for arrays or prefer std::vector"
            })
        
        # Dangling pointer risk
        if re.search(r'return\s+\w+\.c_str\(\)', code):
            issues.append({
                "severity": "HIGH",
                "issue": "Returning c_str() creates dangling pointer",
                "recommendation": "Return std::string instead"
            })
        
        # Buffer overflow risk
        if re.search(r'(strcpy|sprintf|gets)\s*\(', code):
            issues.append({
                "severity": "CRITICAL",
                "issue": "Unsafe C string function detected",
                "recommendation": "Use strncpy, snprintf, or std::string"
            })
        
        # Use after free pattern
        if re.search(r'delete\s+(\w+).*\1\s*=', code, re.DOTALL):
            issues.append({
                "severity": "MEDIUM",
                "issue": "Pointer used after delete without nullification",
                "recommendation": "Set pointer to nullptr after delete or use smart pointers"
            })
        
        # Double delete risk
        if code.count('delete') > 1 and 'unique_ptr' not in code and 'shared_ptr' not in code:
            issues.append({
                "severity": "MEDIUM",
                "issue": "Multiple deletes detected - ensure no double-free",
                "recommendation": "Track ownership carefully or use smart pointers"
            })
        
        return {
            "status": "checked",
            "issues": issues,
            "safe": len(issues) == 0,
            "summary": f"Found {len(issues)} memory safety concern(s)" if issues else "No obvious memory safety issues detected"
        }
