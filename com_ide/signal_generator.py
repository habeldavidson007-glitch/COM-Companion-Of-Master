"""
Signal IR Generator

This module converts AST nodes into Signal IR (Intermediate Representation).
Signal is a deterministic, execution-ready JSON format.
"""

from typing import Dict, Any, List
from eno_ast import ASTNode, Program, Assignment, Variable, Literal, Input, Output, BinaryOp, IfStatement, Loop, FunctionDef, FunctionCall, Return, Break, Exit, PropertyAccess


class SignalGenerator:
    """Converts AST to Signal IR."""
    
    def __init__(self):
        self.signal_id = 0
    
    def generate_id(self) -> int:
        """Generate unique signal ID."""
        self.signal_id += 1
        return self.signal_id
    
    def generate(self) -> Dict[str, Any]:
        """Generate Signal from AST program."""
        pass
    
    def convert_node(self, node: ASTNode) -> Dict[str, Any]:
        """Convert an AST node to Signal format."""
        return node.to_dict()
    
    def convert_program(self, program: Program) -> Dict[str, Any]:
        """Convert entire program to Signal IR."""
        signals = []
        
        for stmt in program.statements:
            signal = self.convert_node(stmt)
            signal["id"] = self.generate_id()
            signals.append(signal)
        
        return {
            "version": "1.0",
            "type": "SIGNAL_PROGRAM",
            "signals": signals
        }


def generate_signal(ast_program: Program) -> Dict[str, Any]:
    """Convenience function to generate Signal IR from AST."""
    generator = SignalGenerator()
    return generator.convert_program(ast_program)
