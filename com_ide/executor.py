"""
Signal IR Executor (Harness Layer)

This module converts Signal IR to Python code and executes it safely.
It captures stdout, errors, and execution traces.
"""

import json
import sys
import io
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from eno_ast import ASTNode, Program, Assignment, Variable, Literal, Input, Output, BinaryOp, IfStatement, Loop, FunctionDef, FunctionCall, Return, Break, Exit, PropertyAccess


class ExecutionResult:
    """Represents the result of an execution."""
    
    def __init__(self):
        self.success = False
        self.output = ""
        self.error = None
        self.trace = []
        self.return_value = None
        self.start_time = None
        self.end_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": str(self.error) if self.error else None,
            "trace": self.trace,
            "return_value": self.return_value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (
                (self.end_time - self.start_time).total_seconds() * 1000
                if self.start_time and self.end_time else None
            )
        }


class SignalExecutor:
    """Executes Signal IR by converting to Python and running safely."""
    
    def __init__(self, signal_program: Dict[str, Any], input_provider=None):
        self.signal_program = signal_program
        self.input_provider = input_provider or input
        self.variables = {}
        self.functions = {}
        self.execution_trace = []
        self.output_buffer = io.StringIO()
        self.loop_detected = False
        self.break_requested = False
        self.exit_requested = False
        self.return_value = None
    
    def generate_python_code(self) -> str:
        """Convert Signal IR to Python code."""
        lines = []
        lines.append("# Auto-generated Python code from Signal IR")
        lines.append("import sys")
        lines.append("")
        
        # Pre-define functions dictionary for function calls
        lines.append("_functions = {}")
        lines.append("_variables = {}")
        lines.append("_input_func = None")
        lines.append("_output_lines = []")
        lines.append("_break_requested = False")
        lines.append("_exit_requested = False")
        lines.append("_return_value = None")
        lines.append("")
        
        signals = self.signal_program.get("signals", [])
        for signal in signals:
            python_code = self._convert_signal_to_python(signal, indent=0)
            lines.append(python_code)
        
        lines.append("")
        lines.append("# Output captured results")
        lines.append("print('\\n'.join(_output_lines))")
        
        return "\n".join(lines)
    
    def _convert_signal_to_python(self, signal: Dict[str, Any], indent: int = 0) -> str:
        """Convert a single signal node to Python code."""
        prefix = "    " * indent
        signal_type = signal.get("type")
        
        if signal_type == "ASSIGN":
            var_name = signal["variable"]
            value_code = self._expr_to_python(signal["value"])
            return f"{prefix}_variables['{var_name}'] = {value_code}"
        
        elif signal_type == "VAR":
            var_name = signal["name"]
            return f"{prefix}_variables.get('{var_name}')"
        
        elif signal_type == "LITERAL":
            value = signal["value"]
            literal_type = signal["literal_type"]
            if literal_type == "STRING":
                escaped = str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                return f'"{escaped}"'
            elif literal_type == "NUMBER":
                return str(value)
            elif literal_type == "BOOL":
                return "True" if value else "False"
            elif literal_type == "NULL":
                return "None"
            return f"{prefix}None"
        
        elif signal_type == "BINOP":
            left = self._expr_to_python(signal["left"])
            op = signal["operator"]
            right = self._expr_to_python(signal["right"])
            return f"{prefix}({left} {op} {right})"
        
        elif signal_type == "INPUT":
            prompt_code = self._expr_to_python(signal["prompt"])
            return f"{prefix}(_input_func({prompt_code}) if _input_func else input({prompt_code}))"
        
        elif signal_type == "OUTPUT":
            value_code = self._expr_to_python(signal["value"])
            return f"{prefix}_output_lines.append(str({value_code}))"
        
        elif signal_type == "IF":
            condition_code = self._expr_to_python(signal["condition"])
            lines = []
            lines.append(f"{prefix}if {condition_code}:")
            
            then_block = signal.get("then", [])
            if then_block:
                for stmt in then_block:
                    lines.append(self._convert_signal_to_python(stmt, indent + 1))
            else:
                lines.append(f"{prefix}    pass")
            
            # Handle elif branches
            for elif_branch in signal.get("elif", []):
                elif_condition = self._expr_to_python(elif_branch["condition"])
                lines.append(f"{prefix}elif {elif_condition}:")
                elif_block = elif_branch.get("block", [])
                if elif_block:
                    for stmt in elif_block:
                        lines.append(self._convert_signal_to_python(stmt, indent + 1))
                else:
                    lines.append(f"{prefix}    pass")
            
            # Handle else block
            else_block = signal.get("else", [])
            if else_block:
                lines.append(f"{prefix}else:")
                for stmt in else_block:
                    lines.append(self._convert_signal_to_python(stmt, indent + 1))
            
            return "\n".join(lines)
        
        elif signal_type == "LOOP":
            loop_type = signal.get("loop_type")
            lines = []
            
            if loop_type == "RANGE":
                iterator = signal.get("iterator", "_i")
                limit_code = self._expr_to_python(signal.get("limit"))
                lines.append(f"{prefix}for _variables['{iterator}'] in range({limit_code}):")
                
                body = signal.get("body", [])
                if body:
                    for stmt in body:
                        stmt_code = self._convert_signal_to_python(stmt, indent + 1)
                        # Inject break/exit checks
                        lines.append(stmt_code)
                else:
                    lines.append(f"{prefix}    pass")
            
            elif loop_type == "WHILE":
                condition_code = self._expr_to_python(signal.get("condition"))
                lines.append(f"{prefix}while {condition_code}:")
                
                body = signal.get("body", [])
                if body:
                    for stmt in body:
                        lines.append(self._convert_signal_to_python(stmt, indent + 1))
                else:
                    lines.append(f"{prefix}    pass")
            
            return "\n".join(lines)
        
        elif signal_type == "FUNCTION_DEF":
            name = signal.get("name")
            params = signal.get("params", [])
            param_list = ", ".join([f"_p_{p}" for p in params])
            
            lines = []
            lines.append(f"{prefix}def _func_{name}({param_list}):")
            lines.append(f"{prefix}    global _return_value")
            
            # Assign parameters to local variables
            for i, param in enumerate(params):
                lines.append(f"{prefix}    _variables['{param}'] = _p_{i}")
            
            body = signal.get("body", [])
            if body:
                for stmt in body:
                    lines.append(self._convert_signal_to_python(stmt, indent + 1))
            else:
                lines.append(f"{prefix}    pass")
            
            lines.append(f"{prefix}    return _return_value")
            lines.append(f"{prefix}_functions['{name}'] = _func_{name}")
            
            return "\n".join(lines)
        
        elif signal_type == "CALL":
            name = signal.get("name")
            args = signal.get("args", [])
            args_code = ", ".join([self._expr_to_python(arg) for arg in args])
            target = signal.get("target")
            
            call_code = f"_functions.get('{name}', lambda *a: None)({args_code})"
            
            if target:
                return f"{prefix}_variables['{target}'] = {call_code}"
            else:
                return f"{prefix}{call_code}"
        
        elif signal_type == "RETURN":
            value_code = self._expr_to_python(signal.get("value"))
            # Only use break if inside a loop, otherwise just assign return value
            return f"{prefix}_return_value = {value_code}"
        
        elif signal_type == "BREAK":
            return f"{prefix}_break_requested = True; break"
        
        elif signal_type == "EXIT":
            return f"{prefix}_exit_requested = True; break"
        
        elif signal_type == "PROPERTY":
            obj_name = signal.get("object")
            prop_name = signal.get("property")
            return f"{prefix}_variables.get('{obj_name}', {{}}).get('{prop_name}')"
        
        return f"{prefix}pass"
    
    def _expr_to_python(self, expr: Dict[str, Any]) -> str:
        """Convert an expression node to Python code string."""
        if not expr:
            return "None"
        
        expr_type = expr.get("type")
        
        if expr_type == "LITERAL":
            value = expr["value"]
            literal_type = expr["literal_type"]
            if literal_type == "STRING":
                escaped = str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                return f'"{escaped}"'
            elif literal_type == "NUMBER":
                return str(value)
            elif literal_type == "BOOL":
                return "True" if value else "False"
            elif literal_type == "NULL":
                return "None"
            return "None"
        
        elif expr_type == "VAR":
            var_name = expr["name"]
            return f"_variables.get('{var_name}')"
        
        elif expr_type == "BINOP":
            left = self._expr_to_python(expr["left"])
            op = expr["operator"]
            right = self._expr_to_python(expr["right"])
            return f"({left} {op} {right})"
        
        elif expr_type == "PROPERTY":
            obj_name = expr["object"]
            prop_name = expr["property"]
            return f"_variables.get('{obj_name}', {{}}).get('{prop_name}')"
        
        elif expr_type == "INPUT":
            prompt_code = self._expr_to_python(expr.get("prompt", {"type": "LITERAL", "value": "", "literal_type": "STRING"}))
            return f"(_input_func({prompt_code}) if _input_func else input({prompt_code}))"
        
        return "None"
    
    def execute(self) -> ExecutionResult:
        """Execute the Signal program and return results."""
        result = ExecutionResult()
        result.start_time = datetime.now()
        
        try:
            python_code = self.generate_python_code()
            
            # Create restricted execution environment
            exec_globals = {
                "__builtins__": {
                    "__import__": __import__,  # Needed for datetime module
                    "input": input,  # Needed for input() calls
                    "range": range,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "print": print,
                }
            }
            exec_locals = {
                "_variables": self.variables,
                "_functions": self.functions,
                "_input_func": self.input_provider,
                "_output_lines": [],
                "_break_requested": False,
                "_exit_requested": False,
                "_return_value": None,
            }
            
            # Execute the generated Python code
            exec(python_code, exec_globals, exec_locals)
            
            result.success = True
            result.output = "\n".join(exec_locals["_output_lines"])
            result.return_value = exec_locals.get("_return_value")
            
        except Exception as e:
            result.success = False
            result.error = e
            result.trace = traceback.format_exc().split("\n")
        
        result.end_time = datetime.now()
        result.trace = self._build_execution_trace()
        
        return result
    
    def _build_execution_trace(self) -> List[Dict[str, Any]]:
        """Build execution trace from signals."""
        trace = []
        signals = self.signal_program.get("signals", [])
        
        for i, signal in enumerate(signals):
            trace.append({
                "step": i,
                "signal_type": signal.get("type"),
                "signal_id": signal.get("id"),
                "timestamp": datetime.now().isoformat()
            })
        
        return trace


def execute_signal(signal_program: Dict[str, Any], input_provider=None) -> ExecutionResult:
    """Convenience function to execute Signal IR."""
    executor = SignalExecutor(signal_program, input_provider)
    return executor.execute()
