"""
E+ Abstract Syntax Tree (AST) Definitions

This module defines the AST node types for the E+ DSL.
Each node type represents a specific construct in the language.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict


class ASTNode(ABC):
    """Base class for all AST nodes."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        pass


class Program(ASTNode):
    """Root node representing the entire program."""
    
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PROGRAM",
            "statements": [stmt.to_dict() for stmt in self.statements]
        }


class Assignment(ASTNode):
    """Variable assignment: @name = (value)"""
    
    def __init__(self, var_name: str, value: ASTNode):
        self.var_name = var_name
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ASSIGN",
            "variable": self.var_name,
            "value": self.value.to_dict()
        }


class Variable(ASTNode):
    """Variable reference: @name"""
    
    def __init__(self, name: str):
        self.name = name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "VAR",
            "name": self.name
        }


class Literal(ASTNode):
    """Literal value: (10), ("Hello"), (True), (False)"""
    
    def __init__(self, value: Any, literal_type: str):
        self.value = value
        self.literal_type = literal_type  # "STRING", "NUMBER", "BOOL", "NULL"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "LITERAL",
            "value": self.value,
            "literal_type": self.literal_type
        }


class Input(ASTNode):
    """Input statement: @var = input("prompt")"""
    
    def __init__(self, prompt: ASTNode):
        self.prompt = prompt
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "INPUT",
            "prompt": self.prompt.to_dict()
        }


class Output(ASTNode):
    """Output statement: say(value)"""
    
    def __init__(self, value: ASTNode):
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "OUTPUT",
            "value": self.value.to_dict()
        }


class BinaryOp(ASTNode):
    """Binary operation: (@a + @b), (@x > 10)"""
    
    def __init__(self, left: ASTNode, operator: str, right: ASTNode):
        self.left = left
        self.operator = operator
        self.right = right
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "BINOP",
            "left": self.left.to_dict(),
            "operator": self.operator,
            "right": self.right.to_dict()
        }


class IfStatement(ASTNode):
    """If/Else statement with optional elif branches."""
    
    def __init__(
        self,
        condition: ASTNode,
        then_block: List[ASTNode],
        elif_branches: List[tuple],  # List of (condition, block) tuples
        else_block: Optional[List[ASTNode]] = None
    ):
        self.condition = condition
        self.then_block = then_block
        self.elif_branches = elif_branches
        self.else_block = else_block or []
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": "IF",
            "condition": self.condition.to_dict(),
            "then": [stmt.to_dict() for stmt in self.then_block],
            "elif": [
                {"condition": c.to_dict(), "block": [s.to_dict() for s in b]}
                for c, b in self.elif_branches
            ],
            "else": [stmt.to_dict() for stmt in self.else_block]
        }
        return result


class Loop(ASTNode):
    """Loop statement: repeat(@i, 10) {} or repeat while(condition) {}"""
    
    def __init__(
        self,
        loop_type: str,  # "RANGE" or "WHILE"
        iterator: Optional[str],
        limit: Optional[ASTNode],
        condition: Optional[ASTNode],
        body: List[ASTNode]
    ):
        self.loop_type = loop_type
        self.iterator = iterator
        self.limit = limit
        self.condition = condition
        self.body = body
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": "LOOP",
            "loop_type": self.loop_type,
            "body": [stmt.to_dict() for stmt in self.body]
        }
        if self.loop_type == "RANGE":
            result["iterator"] = self.iterator
            result["limit"] = self.limit.to_dict() if self.limit else None
        elif self.loop_type == "WHILE":
            result["condition"] = self.condition.to_dict() if self.condition else None
        return result


class FunctionDef(ASTNode):
    """Function definition: function Name(@a, @b) { ... }"""
    
    def __init__(
        self,
        name: str,
        params: List[str],
        body: List[ASTNode]
    ):
        self.name = name
        self.params = params
        self.body = body
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "FUNCTION_DEF",
            "name": self.name,
            "params": self.params,
            "body": [stmt.to_dict() for stmt in self.body]
        }


class FunctionCall(ASTNode):
    """Function call: @result = call Name(arg1, arg2)"""
    
    def __init__(
        self,
        name: str,
        args: List[ASTNode],
        target_var: Optional[str] = None
    ):
        self.name = name
        self.args = args
        self.target_var = target_var
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": "CALL",
            "name": self.name,
            "args": [arg.to_dict() for arg in self.args]
        }
        if self.target_var:
            result["target"] = self.target_var
        return result


class Return(ASTNode):
    """Return statement: return(value)"""
    
    def __init__(self, value: ASTNode):
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "RETURN",
            "value": self.value.to_dict()
        }


class Break(ASTNode):
    """Break statement: break"""
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": "BREAK"}


class Exit(ASTNode):
    """Exit statement: exit"""
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": "EXIT"}


class PropertyAccess(ASTNode):
    """Property access: @car.color"""
    
    def __init__(self, object_name: str, property_name: str):
        self.object_name = object_name
        self.property_name = property_name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PROPERTY",
            "object": self.object_name,
            "property": self.property_name
        }
