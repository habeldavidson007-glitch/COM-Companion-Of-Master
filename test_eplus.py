"""Test suite for E+ Compiler"""

from eplus_compiler import compile_eplus

def test_scenario(name, eplus_code, expected_output=None):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print("E+ Source:")
    print(eplus_code)
    print("\nCompiled Python:")
    result = compile_eplus(eplus_code)
    print(result)
    
    if "COMPILATION ERROR" in result:
        print("❌ COMPILATION FAILED")
        return False
    
    print("\nExecution Output:")
    try:
        exec(result)
        print("✅ SUCCESS")
        return True
    except Exception as e:
        print(f"❌ RUNTIME ERROR: {e}")
        return False

# Test 1: Function with Return
test_scenario("Function with Return", """
[Add](@a, @b) {
    @Result = (@a + @b)
    => (@Result)
}
@Answer = ^[Add](10, 25)
>> (@Answer)
""")

# Test 2: Condition Chain
test_scenario("Condition Chain (if-elif-else)", """
@Age = (20)
? (@Age > 17) {
    >> ("Adult")
} ?? (@Age > 12) {
    >> ("Teen")
} :: {
    >> ("Child")
}
""")

# Test 3: For Loop (Range)
test_scenario("For Loop (Range)", """
@Sum = (0)
@@ (@i, 5) {
    + @Sum (@i)
}
>> (@Sum)
""")

# Test 4: For Each Loop
test_scenario("For Each Loop", """
@Items = [ ]
+@ @Items ("A")
+@ @Items ("B")
+@ @Items ("C")
@@ (@item, @Items) {
    >> (@item)
}
""")

# Test 5: While Loop with Break
test_scenario("While Loop with Break", """
@Count = (5)
@@? (@Count > (0)) {
    >> (@Count)
    - @Count (1)
    ? (@Count == (3)) { ! }
}
""")

# Test 6: Logical Operators
test_scenario("Logical AND/OR", """
@X = (10)
@Y = (20)
? (@X > (5) && @Y < (30)) {
    >> ("Both true")
}
? (@X == (1) || @Y == (20)) {
    >> ("One is true")
}
""")

# Test 7: Arithmetic Operations
test_scenario("Arithmetic Mutations", """
@Score = (100)
+ @Score (50)
- @Score (20)
* @Score (2)
/ @Score (10)
>> (@Score)
""")

# Test 8: Comparison Operators
test_scenario("Comparison Operators", """
@A = (10)
@B = (10)
? (@A == @B) {
    >> ("Equal")
}
? (@A >= @B) {
    >> ("Greater or Equal")
}
? (@A <= @B) {
    >> ("Less or Equal")
}
""")

print("\n\n" + "="*60)
print("ALL TESTS COMPLETED")
print("="*60)
