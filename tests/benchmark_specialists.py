"""
COM Specialist Tools Benchmark Tests
Tests for Python, C++, and Web expert tool integration.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.tool_harness import execute_signal, file_manager, OUTPUT_DIR

def test_python_expert_signal():
    """Test @PY signal execution for Python code generation."""
    signal = "@PY:hello.py:def greet(name):\n    return f'Hello, {name}!'"
    result = execute_signal(signal)
    
    assert result['success'], f"Python expert failed: {result.get('error', 'Unknown error')}"
    assert 'file_path' in result['result'], "No file path returned"
    assert os.path.exists(result['result']['file_path']), "Generated file does not exist"
    assert result['result']['file_path'].startswith(OUTPUT_DIR), f"File not in output dir: {result['result']['file_path']}"
    
    # Verify content
    with open(result['result']['file_path'], 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'def greet' in content, "Generated code missing function definition"
    
    print("✓ Test 1 PASSED: Python expert signal (@PY)")
    return True

def test_cpp_expert_signal():
    """Test @CPP signal execution for C++ code generation."""
    signal = "@CPP:hello.cpp:#include <iostream>\nint main() {\n    std::cout << \"Hello\" << std::endl;\n    return 0;\n}"
    result = execute_signal(signal)
    
    assert result['success'], f"C++ expert failed: {result.get('error', 'Unknown error')}"
    assert 'file_path' in result['result'], "No file path returned"
    assert os.path.exists(result['result']['file_path']), "Generated file does not exist"
    assert result['result']['file_path'].startswith(OUTPUT_DIR), f"File not in output dir"
    
    # Verify content
    with open(result['result']['file_path'], 'r', encoding='utf-8') as f:
        content = f.read()
    assert '#include' in content, "Generated code missing include"
    assert 'int main()' in content, "Generated code missing main function"
    
    print("✓ Test 2 PASSED: C++ expert signal (@CPP)")
    return True

def test_web_expert_signal():
    """Test @WEB signal execution for HTML generation."""
    signal = "@WEB:index.html:<!DOCTYPE html>\n<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
    result = execute_signal(signal)
    
    assert result['success'], f"Web expert failed: {result.get('error', 'Unknown error')}"
    assert 'file_path' in result['result'], "No file path returned"
    assert os.path.exists(result['result']['file_path']), "Generated file does not exist"
    assert result['result']['file_path'].startswith(OUTPUT_DIR), f"File not in output dir"
    
    # Verify content
    with open(result['result']['file_path'], 'r', encoding='utf-8') as f:
        content = f.read()
    assert '<!DOCTYPE html>' in content or '<html>' in content, "Generated code missing HTML structure"
    
    print("✓ Test 3 PASSED: Web expert signal (@WEB)")
    return True

def test_routing_specificity():
    """Test that hierarchical specificity scoring routes correctly."""
    from core.intent_router import IntentRouter
    
    router = IntentRouter()
    
    # Test clear Office routing with phrase match
    mode = router.route("create a pdf report")
    assert mode == "OFFICE", f"Expected OFFICE, got {mode}"
    
    # Test clear Godot routing with phrase match
    mode = router.route("godot game scene")
    assert mode == "GODOT", f"Expected GODOT, got {mode}"
    
    # Test Python routing
    mode = router.route("python script with flask")
    assert mode == "PYTHON", f"Expected PYTHON, got {mode}"
    
    print("✓ Test 4 PASSED: Routing specificity scoring")
    return True

def test_safe_write_security():
    """Test that safe_write prevents directory traversal."""
    # Try to write outside output directory
    result = file_manager.safe_write(
        "../../../etc/passwd", 
        "malicious content", 
        ".txt"
    )
    
    # Should either fail safely or redirect to safe path
    if result['success']:
        # If it succeeded, verify the path is still within OUTPUT_DIR
        assert result['file_path'].startswith(OUTPUT_DIR), \
            f"Security breach: file written outside output dir: {result['file_path']}"
    
    # Test normal safe write
    result = file_manager.safe_write("test_secure.txt", "safe content", "")
    assert result['success'], f"Safe write failed: {result.get('error')}"
    assert os.path.exists(result['file_path']), "Safe write did not create file"
    assert result['file_path'].startswith(OUTPUT_DIR), "Safe write outside output dir"
    
    print("✓ Test 5 PASSED: Safe write security")
    return True

def run_all_tests():
    """Run all specialist tool benchmark tests."""
    print("\n" + "="*60)
    print("COM SPECIALIST TOOLS BENCHMARK")
    print("="*60 + "\n")
    
    tests = [
        test_python_expert_signal,
        test_cpp_expert_signal,
        test_web_expert_signal,
        test_routing_specificity,
        test_safe_write_security
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed == 0:
        print("STATUS: ALL TESTS PASSED ✓")
    else:
        print(f"STATUS: {failed} tests failed ✗")
    print("="*60 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
