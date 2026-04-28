"""
JSON Expert Module for COM
Specialized in JSON parsing, validation, transformation, schema generation, and best practices.
"""

import json
import re
from typing import Dict, List, Any, Optional, Union
from tools.base import BaseTool


class JsonExpertTool(BaseTool):
    """Tool for JSON development assistance."""
    
    def __init__(self):
        super().__init__()
        self.name = "JsonExpertTool"
        self.description = "Expert in JSON: parsing, validation, schema generation, transformation, optimization, and best practices."
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute JSON-related tasks.
        
        Actions:
        - 'validate': Validate JSON syntax and structure
        - 'format': Format/beautify JSON
        - 'minify': Minify JSON
        - 'transform': Transform JSON structure
        - 'extract': Extract specific paths from JSON
        - 'generate_schema': Generate JSON Schema from data
        - 'explain': Explain JSON concepts
        - 'compare': Compare two JSON objects
        """
        if action == "validate":
            return self.validate_json(kwargs.get("json_data", ""))
        elif action == "format":
            return self.format_json(kwargs.get("json_data", ""), kwargs.get("indent", 2))
        elif action == "minify":
            return self.minify_json(kwargs.get("json_data", ""))
        elif action == "transform":
            return self.transform_json(kwargs.get("json_data", ""), kwargs.get("mapping", {}))
        elif action == "extract":
            return self.extract_path(kwargs.get("json_data", ""), kwargs.get("path", ""))
        elif action == "generate_schema":
            return self.generate_schema(kwargs.get("json_data", ""))
        elif action == "explain":
            return self.explain_concept(kwargs.get("concept", ""))
        elif action == "compare":
            return self.compare_json(kwargs.get("json1", ""), kwargs.get("json2", ""))
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "validate", "format", "minify", "transform", 
                "extract", "generate_schema", "explain", "compare"
            ]}
    
    def validate_json(self, json_data: Union[str, Dict, List]) -> Dict[str, Any]:
        """Validate JSON syntax and structure."""
        try:
            # If string, parse it
            if isinstance(json_data, str):
                parsed = json.loads(json_data)
            else:
                parsed = json_data
            
            # Basic validation checks
            issues = []
            warnings = []
            
            # Check for common issues
            json_str = json.dumps(parsed)
            
            # Check for very large nesting
            def check_depth(obj, depth=0, max_depth=0):
                if isinstance(obj, dict):
                    max_depth = max(max_depth, depth + 1)
                    for v in obj.values():
                        max_depth = check_depth(v, depth + 1, max_depth)
                elif isinstance(obj, list):
                    max_depth = max(max_depth, depth + 1)
                    for item in obj:
                        max_depth = check_depth(item, depth + 1, max_depth)
                return max_depth
            
            max_nesting = check_depth(parsed)
            if max_nesting > 10:
                warnings.append(f"Deep nesting detected: {max_nesting} levels (consider flattening)")
            
            # Check for empty structures
            def find_empty(obj, path=""):
                empties = []
                if isinstance(obj, dict):
                    if not obj:
                        empties.append(f"Empty object at {path or 'root'}")
                    for k, v in obj.items():
                        empties.extend(find_empty(v, f"{path}.{k}" if path else k))
                elif isinstance(obj, list):
                    if not obj:
                        empties.append(f"Empty array at {path or 'root'}")
                    for i, item in enumerate(obj):
                        empties.extend(find_empty(item, f"{path}[{i}]"))
                return empties
            
            empty_structures = find_empty(parsed)
            if empty_structures:
                warnings.extend(empty_structures[:5])  # Limit to first 5
            
            return {
                "valid": True,
                "status": "valid",
                "type": type(parsed).__name__,
                "size_bytes": len(json_str),
                "max_nesting_depth": max_nesting,
                "warnings": warnings,
                "issues": issues,
                "preview": json_str[:200] + "..." if len(json_str) > 200 else json_str
            }
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "status": "invalid",
                "error_type": "JSONDecodeError",
                "error_message": str(e),
                "error_position": {"line": e.lineno, "column": e.colno},
                "suggestion": "Check for missing commas, quotes, or brackets"
            }
        except Exception as e:
            return {
                "valid": False,
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
    
    def format_json(self, json_data: Union[str, Dict, List], indent: int = 2) -> Dict[str, Any]:
        """Format/beautify JSON with proper indentation."""
        try:
            if isinstance(json_data, str):
                parsed = json.loads(json_data)
            else:
                parsed = json_data
            
            formatted = json.dumps(parsed, indent=indent, ensure_ascii=False, sort_keys=False)
            
            return {
                "status": "formatted",
                "formatted_json": formatted,
                "original_size": len(json.dumps(parsed, separators=(',', ':'))),
                "formatted_size": len(formatted),
                "indent_used": indent
            }
            
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}", "status": "failed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def minify_json(self, json_data: Union[str, Dict, List]) -> Dict[str, Any]:
        """Minify JSON by removing whitespace."""
        try:
            if isinstance(json_data, str):
                parsed = json.loads(json_data)
            else:
                parsed = json_data
            
            minified = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
            original_size = len(json.dumps(parsed, indent=2))
            
            return {
                "status": "minified",
                "minified_json": minified,
                "original_size": original_size,
                "minified_size": len(minified),
                "reduction_percent": round((1 - len(minified)/original_size) * 100, 2) if original_size > 0 else 0
            }
            
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}", "status": "failed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def transform_json(self, json_data: Union[str, Dict, List], mapping: Dict) -> Dict[str, Any]:
        """Transform JSON structure based on mapping."""
        try:
            if isinstance(json_data, str):
                parsed = json.loads(json_data)
            else:
                parsed = json_data
            
            def apply_mapping(data, map_rule):
                if isinstance(map_rule, str):
                    # Simple field mapping
                    if map_rule.startswith("$."):
                        path = map_rule[2:].split(".")
                        result = data
                        for p in path:
                            if isinstance(result, dict) and p in result:
                                result = result[p]
                            else:
                                return None
                        return result
                    return map_rule
                elif isinstance(map_rule, dict):
                    # Object mapping
                    return {k: apply_mapping(data, v) for k, v in map_rule.items()}
                elif isinstance(map_rule, list):
                    # Array mapping
                    return [apply_mapping(data, item) for item in map_rule]
                return map_rule
            
            transformed = apply_mapping(parsed, mapping)
            
            return {
                "status": "transformed",
                "transformed_json": transformed,
                "mapping_applied": mapping
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def extract_path(self, json_data: Union[str, Dict, List], path: str) -> Dict[str, Any]:
        """Extract specific paths from JSON using dot notation or JSONPath-like syntax."""
        try:
            if isinstance(json_data, str):
                parsed = json.loads(json_data)
            else:
                parsed = json_data
            
            # Handle JSONPath-like syntax
            if path.startswith("$."):
                path = path[2:]
            
            parts = re.split(r'\.|\[|\]', path)
            parts = [p for p in parts if p]  # Remove empty strings
            
            current = parsed
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list):
                    try:
                        index = int(part)
                        current = current[index]
                    except (ValueError, IndexError):
                        return {"error": f"Invalid array index: {part}", "status": "failed"}
                else:
                    return {"error": f"Path not found: {path}", "status": "failed"}
            
            return {
                "status": "extracted",
                "path": path,
                "value": current,
                "value_type": type(current).__name__
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def generate_schema(self, json_data: Union[str, Dict, List]) -> Dict[str, Any]:
        """Generate JSON Schema from sample data."""
        try:
            if isinstance(json_data, str):
                parsed = json.loads(json_data)
            else:
                parsed = json_data
            
            def infer_type(value) -> str:
                if value is None:
                    return "null"
                elif isinstance(value, bool):
                    return "boolean"
                elif isinstance(value, int):
                    return "integer"
                elif isinstance(value, float):
                    return "number"
                elif isinstance(value, str):
                    return "string"
                elif isinstance(value, list):
                    return "array"
                elif isinstance(value, dict):
                    return "object"
                return "unknown"
            
            def generate_schema_for_value(value, seen_types=None) -> Dict:
                if seen_types is None:
                    seen_types = set()
                
                value_type = infer_type(value)
                schema = {"type": value_type}
                
                if value_type == "object" and isinstance(value, dict):
                    properties = {}
                    required = []
                    for key, val in value.items():
                        properties[key] = generate_schema_for_value(val, seen_types)
                        required.append(key)
                    
                    schema["properties"] = properties
                    if required:
                        schema["required"] = required
                
                elif value_type == "array" and isinstance(value, list) and value:
                    # Infer items schema from first element
                    schema["items"] = generate_schema_for_value(value[0], seen_types)
                    schema["minItems"] = len(value)
                    schema["maxItems"] = len(value)
                
                elif value_type == "string":
                    schema["minLength"] = 0
                    schema["maxLength"] = len(value)
                
                elif value_type in ("integer", "number"):
                    schema["minimum"] = value
                    schema["maximum"] = value
                
                return schema
            
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Generated Schema",
                "description": "Automatically generated JSON Schema from sample data",
                **generate_schema_for_value(parsed)
            }
            
            return {
                "status": "generated",
                "schema": schema,
                "schema_json": json.dumps(schema, indent=2)
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def explain_concept(self, concept: str) -> str:
        """Explain JSON concepts."""
        concept_lower = concept.lower()
        
        explanations = {
            "syntax": """
JSON Syntax Basics:
===================
JSON (JavaScript Object Notation) is a lightweight data-interchange format.

Basic Rules:
1. Data is in name/value pairs: {"name": "value"}
2. Data is separated by commas
3. Curly braces hold objects: {}
4. Square brackets hold arrays: []
5. Keys must be strings in double quotes
6. Values can be: string, number, object, array, true, false, null

Example:
{
  "name": "John",
  "age": 30,
  "isStudent": false,
  "courses": ["Math", "Science"],
  "address": {
    "city": "New York",
    "zip": "10001"
  }
}
""",
            "schema": """
JSON Schema:
============
JSON Schema is a vocabulary for validating JSON data.

Key Keywords:
- type: Defines the data type (string, number, integer, object, array, boolean, null)
- properties: Defines properties of an object
- required: Lists required properties
- items: Defines schema for array items
- minimum/maximum: Numeric constraints
- minLength/maxLength: String constraints
- pattern: Regex pattern for strings
- enum: List of allowed values

Example:
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {"type": "string", "minLength": 1},
    "age": {"type": "integer", "minimum": 0, "maximum": 150},
    "email": {"type": "string", "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
    "role": {"type": "string", "enum": ["admin", "user", "guest"]}
  },
  "required": ["name", "age"]
}
""",
            "validation": """
JSON Validation:
================
Validation ensures JSON data conforms to expected structure and rules.

Common Validation Checks:
1. Syntax validation: Proper JSON format
2. Schema validation: Conforms to JSON Schema
3. Type checking: Correct data types
4. Required fields: All mandatory fields present
5. Range validation: Numbers within acceptable range
6. Pattern matching: Strings match expected patterns
7. Enum validation: Values from allowed list

Tools:
- Ajv (JavaScript)
- jsonschema (Python)
- Newtonsoft.Json (.NET)
- Online validators: jsonlint.com, jsonschemavalidator.net
""",
            "best_practices": """
JSON Best Practices:
====================

1. Use meaningful keys:
   ✓ {"firstName": "John"}
   ✗ {"fn": "John"}

2. Keep it flat when possible:
   ✓ {"city": "NYC", "zip": "10001"}
   ✗ {"location": {"city": "NYC", "details": {"zip": "10001"}}}

3. Use arrays for lists:
   ✓ {"tags": ["json", "data"]}
   ✗ {"tag1": "json", "tag2": "data"}

4. Be consistent with naming:
   ✓ camelCase or snake_case throughout
   ✗ Mixing firstName and last_name

5. Avoid comments in production JSON:
   - JSON doesn't support comments
   - Use separate documentation if needed

6. Handle null explicitly:
   ✓ {"middleName": null}
   ✗ Omitting the field entirely (if it's expected)

7. Use appropriate types:
   ✓ {"age": 30} (number)
   ✗ {"age": "30"} (string)

8. Keep payloads small:
   - Minify for transmission
   - Remove unnecessary whitespace
   - Use abbreviations carefully
""",
            "jsonpath": """
JSONPath:
=========
JSONPath is a query language for JSON, similar to XPath for XML.

Basic Syntax:
- $ : Root element
- . or [] : Child operator
- * : Wildcard (all elements)
- .. : Recursive descent
- [n] : Array index
- [start:end] : Array slice
- [,] : Union
- ?() : Filter expression

Examples:
$.store.book[*].author    - All authors in store books
$..price                  - All prices anywhere
$.store.bicycle.price     - Price of bicycle
$.book[0]                 - First book
$.book[-1]                - Last book
$.book[0:2]               - First two books
$..book[?(@.price < 10)]  - Books under $10
$..*[?(@.isbn)]           - All items with ISBN

Libraries:
- jsonpath-ng (Python)
- jsonpath-plus (JavaScript)
- Jayway JsonPath (Java)
"""
        }
        
        for key, explanation in explanations.items():
            if key in concept_lower or key.replace('_', ' ') in concept_lower:
                return explanation
        
        return f"Concept '{concept}' not found. Try: syntax, schema, validation, best_practices, jsonpath"
    
    def compare_json(self, json1: Union[str, Dict], json2: Union[str, Dict]) -> Dict[str, Any]:
        """Compare two JSON objects and identify differences."""
        try:
            if isinstance(json1, str):
                data1 = json.loads(json1)
            else:
                data1 = json1
            
            if isinstance(json2, str):
                data2 = json.loads(json2)
            else:
                data2 = json2
            
            differences = []
            
            def compare_recursive(obj1, obj2, path=""):
                if type(obj1) != type(obj2):
                    differences.append({
                        "path": path or "root",
                        "issue": "type_mismatch",
                        "value1": type(obj1).__name__,
                        "value2": type(obj2).__name__
                    })
                    return
                
                if isinstance(obj1, dict):
                    all_keys = set(obj1.keys()) | set(obj2.keys())
                    for key in all_keys:
                        new_path = f"{path}.{key}" if path else key
                        if key not in obj1:
                            differences.append({
                                "path": new_path,
                                "issue": "missing_in_first",
                                "value": obj2[key]
                            })
                        elif key not in obj2:
                            differences.append({
                                "path": new_path,
                                "issue": "missing_in_second",
                                "value": obj1[key]
                            })
                        else:
                            compare_recursive(obj1[key], obj2[key], new_path)
                
                elif isinstance(obj1, list):
                    if len(obj1) != len(obj2):
                        differences.append({
                            "path": path or "root",
                            "issue": "array_length_mismatch",
                            "length1": len(obj1),
                            "length2": len(obj2)
                        })
                    
                    for i in range(min(len(obj1), len(obj2))):
                        compare_recursive(obj1[i], obj2[i], f"{path}[{i}]")
                
                else:
                    if obj1 != obj2:
                        differences.append({
                            "path": path or "root",
                            "issue": "value_mismatch",
                            "value1": obj1,
                            "value2": obj2
                        })
            
            compare_recursive(data1, data2)
            
            return {
                "status": "compared",
                "are_equal": len(differences) == 0,
                "total_differences": len(differences),
                "differences": differences[:20],  # Limit output
                "summary": {
                    "missing_in_first": sum(1 for d in differences if d["issue"] == "missing_in_first"),
                    "missing_in_second": sum(1 for d in differences if d["issue"] == "missing_in_second"),
                    "value_mismatches": sum(1 for d in differences if d["issue"] == "value_mismatch"),
                    "type_mismatches": sum(1 for d in differences if d["issue"] == "type_mismatch")
                }
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
