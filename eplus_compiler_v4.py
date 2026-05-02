"""
COM IDE — E+ Compiler v4.0
Deterministic Compiler for E+ Language (v4 Specification)

Grammar: Keywords express intent, Symbols enforce structure
Pipeline: Lexer → Parser (AST) → Semantic Analyzer → Python Code Generator

E+ v4 Core Principles:
- No symbol overloading (one symbol = one role)
- Fully deterministic (1:1 mapping to Signal IR)
- Canonical keywords with optional shorthand for I/O
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from enum import Enum, auto


# =============================================================================
# 1. LEXER (Tokenization)
# =============================================================================

class TokenType(Enum):
    # Literals & Identifiers
    IDENT = auto()      # Add, Admin
    NUMBER = auto()     # 25, 10
    STRING = auto()     # "Hello"
    VAR = auto()        # @name
    
    # Keywords (Canonical)
    IF = auto()         # if
    ELSE = auto()       # else
    REPEAT = auto()     # repeat
    WHILE = auto()     # while
    FUNCTION = auto()   # function
    CALL = auto()       # call
    RETURN = auto()     # return
    BREAK = auto()      # break
    EXIT = auto()       # exit
    LIST = auto()       # list
    APPEND = auto()     # append
    INPUT = auto()      # input
    SAY = auto()        # say
    
    # Shorthand (Contextual)
    SHORTHAND_IN = auto()   # <
    SHORTHAND_OUT = auto()  # >
    
    # Operators
    EQUALS = auto()     # =
    PLUS = auto()       # +
    MINUS = auto()      # -
    STAR = auto()       # *
    SLASH = auto()      # /
    DOT = auto()        # .
    
    # Comparators
    GT = auto()         # >
    LT = auto()         # <
    GTE = auto()        # >=
    LTE = auto()        # <=
    EQ = auto()         # ==
    NEQ = auto()        # !=
    
    # Logic
    AND = auto()        # and
    OR = auto()         # or
    
    # Delimiters
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    COMMA = auto()      # ,
    
    # Comments
    COMMENT = auto()    # # ...
    
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int


class Lexer:
    KEYWORDS = {
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'repeat': TokenType.REPEAT,
        'while': TokenType.WHILE,
        'function': TokenType.FUNCTION,
        'call': TokenType.CALL,
        'return': TokenType.RETURN,
        'break': TokenType.BREAK,
        'exit': TokenType.EXIT,
        'list': TokenType.LIST,
        'append': TokenType.APPEND,
        'input': TokenType.INPUT,
        'say': TokenType.SAY,
        'and': TokenType.AND,
        'or': TokenType.OR,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def error(self, msg: str):
        raise SyntaxError(f"Lexer Error at line {self.line}, col {self.column}: {msg}")
    
    def peek(self) -> str:
        if self.pos >= len(self.source):
            return '\0'
        return self.source[self.pos]
    
    def advance(self) -> str:
        ch = self.peek()
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch
    
    def skip_whitespace_and_comments(self):
        while True:
            ch = self.peek()
            if ch in ' \t\n\r':
                self.advance()
            elif ch == '#':
                # Skip comment until end of line
                while self.peek() != '\n' and self.peek() != '\0':
                    self.advance()
            else:
                break
    
    def read_string(self) -> str:
        quote = self.advance()  # consume opening "
        result = ""
        while self.peek() != '"' and self.peek() != '\0':
            if self.peek() == '\\':
                self.advance()
                esc = self.advance()
                if esc == 'n': result += '\n'
                elif esc == 't': result += '\t'
                elif esc == '"': result += '"'
                elif esc == '\\': result += '\\'
                else: self.error(f"Invalid escape sequence: \\{esc}")
            else:
                result += self.advance()
        if self.peek() == '\0':
            self.error("Unterminated string")
        self.advance()  # consume closing "
        return result
    
    def read_number(self) -> int:
        start = self.pos
        while self.peek().isdigit():
            self.advance()
        return int(self.source[start:self.pos])
    
    def read_identifier(self) -> str:
        start = self.pos
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        return self.source[start:self.pos]
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
            
            ch = self.peek()
            start_line, start_col = self.line, self.column
            
            # Variable: @identifier
            if ch == '@':
                self.advance()
                ident = self.read_identifier()
                if not ident:
                    self.error("Expected identifier after @")
                self.tokens.append(Token(TokenType.VAR, f"@{ident}", start_line, start_col))
            
            # String: "..."
            elif ch == '"':
                s = self.read_string()
                self.tokens.append(Token(TokenType.STRING, s, start_line, start_col))
            
            # Number
            elif ch.isdigit():
                num = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, num, start_line, start_col))
            
            # Identifier or Keyword
            elif ch.isalpha() or ch == '_':
                ident = self.read_identifier()
                token_type = self.KEYWORDS.get(ident, TokenType.IDENT)
                self.tokens.append(Token(token_type, ident, start_line, start_col))
            
            # Two-character operators
            elif ch == '=' and self.source[self.pos:self.pos+2] == '==':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
            elif ch == '!' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.NEQ, '!=', start_line, start_col))
            elif ch == '>' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.GTE, '>=', start_line, start_col))
            elif ch == '<' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.LTE, '<=', start_line, start_col))
            
            # Single-character operators & delimiters
            elif ch == '=':
                self.advance()
                self.tokens.append(Token(TokenType.EQUALS, '=', start_line, start_col))
            elif ch == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, '+', start_line, start_col))
            elif ch == '-':
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, '-', start_line, start_col))
            elif ch == '*':
                self.advance()
                self.tokens.append(Token(TokenType.STAR, '*', start_line, start_col))
            elif ch == '/':
                self.advance()
                self.tokens.append(Token(TokenType.SLASH, '/', start_line, start_col))
            elif ch == '.':
                self.advance()
                self.tokens.append(Token(TokenType.DOT, '.', start_line, start_col))
            elif ch == '>':
                # Could be GT or SHORTHAND_OUT - context determines
                self.advance()
                self.tokens.append(Token(TokenType.GT, '>', start_line, start_col))
            elif ch == '<':
                # Could be LT or SHORTHAND_IN - context determines
                # For now, tokenize as LT; parser will handle context
                self.advance()
                self.tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            elif ch == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
            elif ch == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
            elif ch == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
            elif ch == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
            elif ch == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
            
            else:
                self.error(f"Unexpected character: '{ch}'")
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens


# =============================================================================
# 2. AST NODES
# =============================================================================

@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

@dataclass
class Assign(ASTNode):
    target: str  # variable name without @
    value: ASTNode

@dataclass
class InputStmt(ASTNode):
    target: str
    prompt: str

@dataclass
class OutputStmt(ASTNode):
    value: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_block: List[ASTNode]
    elif_blocks: List[tuple] = field(default_factory=list)  # [(condition, block), ...]
    else_block: Optional[List[ASTNode]] = None

@dataclass
class LoopRange(ASTNode):
    var: str
    count: ASTNode
    body: List[ASTNode]

@dataclass
class LoopForeach(ASTNode):
    var: str
    collection: str
    body: List[ASTNode]

@dataclass
class LoopWhile(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]
    assign_to: Optional[str] = None

@dataclass
class ReturnStmt(ASTNode):
    value: ASTNode

@dataclass
class BreakStmt(ASTNode):
    pass

@dataclass
class ExitStmt(ASTNode):
    pass

@dataclass
class ListCreate(ASTNode):
    target: str

@dataclass
class ListAppend(ASTNode):
    target: str
    value: ASTNode

@dataclass
class PropertyAccess(ASTNode):
    obj: str
    prop: str

@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class Number(ASTNode):
    value: int

@dataclass
class StringLit(ASTNode):
    value: str

@dataclass
class VarRef(ASTNode):
    name: str


# =============================================================================
# 3. PARSER (Recursive Descent)
# =============================================================================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def error(self, msg: str):
        tok = self.current()
        raise SyntaxError(f"Parser Error at line {tok.line}, col {tok.column}: {msg}")
    
    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]
    
    def advance(self) -> Token:
        tok = self.current()
        self.pos += 1
        return tok
    
    def expect(self, token_type: TokenType, msg: str = None) -> Token:
        if self.current().type != token_type:
            self.error(msg or f"Expected {token_type.name}, got {self.current().type.name}")
        return self.advance()
    
    def match(self, *types: TokenType) -> bool:
        return self.current().type in types
    
    def parse(self) -> Program:
        program = Program()
        while not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                program.statements.append(stmt)
        return program
    
    def parse_statement(self) -> Optional[ASTNode]:
        if self.match(TokenType.VAR):
            return self.parse_assignment_or_call()
        elif self.match(TokenType.IF):
            return self.parse_if()
        elif self.match(TokenType.REPEAT):
            return self.parse_loop()
        elif self.match(TokenType.FUNCTION):
            return self.parse_function_def()
        elif self.match(TokenType.SAY):
            return self.parse_output()
        elif self.match(TokenType.INPUT):
            return self.parse_input()
        elif self.match(TokenType.LIST):
            return self.parse_list_create()
        elif self.match(TokenType.APPEND):
            return self.parse_list_append()
        elif self.match(TokenType.RETURN):
            return self.parse_return()
        elif self.match(TokenType.BREAK):
            self.advance()
            return BreakStmt()
        elif self.match(TokenType.EXIT):
            self.advance()
            return ExitStmt()
        elif self.match(TokenType.GT):
            # Standalone > could be shorthand output: > ("text")
            # Check if followed by LPAREN
            if self.peek(1).type == TokenType.LPAREN:
                return self.parse_shorthand_output()
            self.error("Unexpected '>' - did you mean '>>' for output?")
        elif self.match(TokenType.LT):
            # Shorthand < can only appear in assignment context
            self.error("Shorthand '<' can only be used in variable assignment (e.g., @var = < (\"prompt\"))")
        else:
            self.error(f"Unexpected token: {self.current().type.name}")
    
    def parse_assignment_or_call(self) -> ASTNode:
        var_tok = self.expect(TokenType.VAR)
        var_name = var_tok.value[1:]  # strip @
        
        if self.match(TokenType.EQUALS):
            self.advance()  # consume =
            
            # Check for shorthand input: @var = < (...) or @var = > (...)
            # Note: < and > are tokenized as LT and GT, we need to handle them here
            if self.match(TokenType.LT):
                self.advance()  # consume <
                self.expect(TokenType.LPAREN)
                prompt_tok = self.expect(TokenType.STRING)
                self.expect(TokenType.RPAREN)
                return InputStmt(var_name, prompt_tok.value)
            
            # Check for call: @var = call Func(...)
            if self.match(TokenType.CALL):
                self.advance()  # consume call
                name_tok = self.expect(TokenType.IDENT)
                self.expect(TokenType.LPAREN)
                args = self.parse_arg_list()
                self.expect(TokenType.RPAREN)
                return FunctionCall(name_tok.value, args, assign_to=var_name)
            
            # Regular assignment: @var = expr
            expr = self.parse_expression()
            
            # Handle special cases where expr is InputStmt or ListCreate from factor
            if isinstance(expr, InputStmt):
                return InputStmt(var_name, expr.prompt)
            elif isinstance(expr, ListCreate):
                return ListCreate(var_name)
            
            return Assign(var_name, expr)
        
        # Property access standalone: @car.color
        if self.match(TokenType.DOT):
            self.advance()
            prop_tok = self.expect(TokenType.IDENT)
            return PropertyAccess(var_name, prop_tok.value)
        
        self.error("Expected '=' after variable")
    
    def parse_input(self) -> InputStmt:
        self.advance()  # consume input
        self.expect(TokenType.LPAREN)
        prompt_tok = self.expect(TokenType.STRING)
        self.expect(TokenType.RPAREN)
        # Input must be assigned
        if not self.match(TokenType.VAR):
            self.error("Input statement must be assigned to a variable")
        # This case is handled in parse_assignment_or_call
        self.error("Invalid input syntax")
    
    def parse_output(self) -> OutputStmt:
        self.advance()  # consume say
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        return OutputStmt(expr)
    
    def parse_shorthand_output(self) -> OutputStmt:
        self.advance()  # consume > (tokenized as GT when standalone)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        return OutputStmt(expr)
    
    def parse_list_create(self) -> ListCreate:
        self.advance()  # consume list
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.RPAREN)
        # Must be assigned
        self.error("List creation must be assigned to a variable")
    
    def parse_list_append(self) -> ListAppend:
        self.advance()  # consume append
        self.expect(TokenType.LPAREN)
        var_tok = self.expect(TokenType.VAR)
        self.expect(TokenType.COMMA)
        value = self.parse_expression()
        self.expect(TokenType.RPAREN)
        return ListAppend(var_tok.value[1:], value)
    
    def parse_if(self) -> IfStmt:
        self.advance()  # consume if
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        then_block = self.parse_block()
        
        elif_blocks = []
        while self.match(TokenType.ELSE) and self.peek(1).type == TokenType.IF:
            self.advance()  # else
            self.advance()  # if
            self.expect(TokenType.LPAREN)
            elif_cond = self.parse_expression()
            self.expect(TokenType.RPAREN)
            elif_block = self.parse_block()
            elif_blocks.append((elif_cond, elif_block))
        
        else_block = None
        if self.match(TokenType.ELSE):
            self.advance()
            else_block = self.parse_block()
        
        return IfStmt(condition, then_block, elif_blocks, else_block)
    
    def parse_loop(self) -> ASTNode:
        self.advance()  # consume repeat
        
        if self.match(TokenType.WHILE):
            self.advance()  # consume while
            self.expect(TokenType.LPAREN)
            condition = self.parse_expression()
            self.expect(TokenType.RPAREN)
            body = self.parse_block()
            return LoopWhile(condition, body)
        
        self.expect(TokenType.LPAREN)
        var_tok = self.expect(TokenType.VAR)
        var_name = var_tok.value[1:]
        self.expect(TokenType.COMMA)
        
        if self.match(TokenType.NUMBER):
            count_tok = self.advance()
            self.expect(TokenType.RPAREN)
            body = self.parse_block()
            return LoopRange(var_name, Number(count_tok.value), body)
        elif self.match(TokenType.VAR):
            coll_tok = self.advance()
            self.expect(TokenType.RPAREN)
            body = self.parse_block()
            return LoopForeach(var_name, coll_tok.value[1:], body)
        else:
            self.error("Expected number or variable in loop")
    
    def parse_function_def(self) -> FunctionDef:
        self.advance()  # consume function
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.LPAREN)
        
        params = []
        if self.match(TokenType.VAR):
            var_tok = self.advance()
            params.append(var_tok.value[1:])
            while self.match(TokenType.COMMA):
                self.advance()
                var_tok = self.expect(TokenType.VAR)
                params.append(var_tok.value[1:])
        
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        return FunctionDef(name_tok.value, params, body)
    
    def parse_return(self) -> ReturnStmt:
        self.advance()  # consume return
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        return ReturnStmt(expr)
    
    def parse_block(self) -> List[ASTNode]:
        self.expect(TokenType.LBRACE)
        stmts = []
        while not self.match(TokenType.RBRACE) and not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
        self.expect(TokenType.RBRACE)
        return stmts
    
    def parse_arg_list(self) -> List[ASTNode]:
        args = []
        if not self.match(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                self.advance()
                args.append(self.parse_expression())
        return args
    
    def parse_expression(self) -> ASTNode:
        return self.parse_or_expr()
    
    def parse_or_expr(self) -> ASTNode:
        left = self.parse_and_expr()
        while self.match(TokenType.OR):
            op_tok = self.advance()
            right = self.parse_and_expr()
            left = BinaryOp(left, op_tok.value, right)
        return left
    
    def parse_and_expr(self) -> ASTNode:
        left = self.parse_comparison()
        while self.match(TokenType.AND):
            op_tok = self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left, op_tok.value, right)
        return left
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()
        while self.match(TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE, TokenType.EQ, TokenType.NEQ):
            op_tok = self.advance()
            right = self.parse_additive()
            left = BinaryOp(left, op_tok.value, right)
        return left
    
    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op_tok = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left, op_tok.value, right)
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_factor()
        while self.match(TokenType.STAR, TokenType.SLASH):
            op_tok = self.advance()
            right = self.parse_factor()
            left = BinaryOp(left, op_tok.value, right)
        return left
    
    def parse_factor(self) -> ASTNode:
        if self.match(TokenType.NUMBER):
            tok = self.advance()
            return Number(tok.value)
        elif self.match(TokenType.STRING):
            tok = self.advance()
            return StringLit(tok.value)
        elif self.match(TokenType.VAR):
            tok = self.advance()
            var_name = tok.value[1:]
            # Check for property access: @obj.prop
            if self.match(TokenType.DOT):
                self.advance()
                prop_tok = self.expect(TokenType.IDENT)
                return PropertyAccess(var_name, prop_tok.value)
            return VarRef(var_name)
        elif self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        elif self.match(TokenType.INPUT):
            # Handle input() as function call in expression context
            self.advance()
            self.expect(TokenType.LPAREN)
            prompt_tok = self.expect(TokenType.STRING)
            self.expect(TokenType.RPAREN)
            # Return a special node that will be handled in assignment
            return InputStmt("", prompt_tok.value)
        elif self.match(TokenType.LIST):
            # Handle list() as function call
            self.advance()
            self.expect(TokenType.LPAREN)
            self.expect(TokenType.RPAREN)
            return ListCreate("")
        elif self.match(TokenType.SHORTHAND_IN):
            # Handle shorthand < (...) in expression context (for assignments)
            self.advance()
            self.expect(TokenType.LPAREN)
            prompt_tok = self.expect(TokenType.STRING)
            self.expect(TokenType.RPAREN)
            return InputStmt("", prompt_tok.value)
        else:
            self.error(f"Unexpected token in expression: {self.current().type.name}")


# =============================================================================
# 4. CODE GENERATOR (Python 3)
# =============================================================================

class CodeGenerator:
    def __init__(self):
        self.indent_level = 0
    
    def indent(self) -> str:
        return "    " * self.indent_level
    
    def generate(self, program: Program) -> str:
        lines = []
        for stmt in program.statements:
            self.generate_statement(stmt, lines)
        return "\n".join(lines)
    
    def generate_statement(self, stmt: ASTNode, lines: List[str]):
        if isinstance(stmt, Assign):
            val = self.generate_expr(stmt.value)
            lines.append(f"{self.indent()}{stmt.target} = {val}")
        
        elif isinstance(stmt, InputStmt):
            prompt = stmt.prompt.replace('"', '\\"')
            lines.append(f'{self.indent()}{stmt.target} = int(input("{prompt}"))')
        
        elif isinstance(stmt, OutputStmt):
            val = self.generate_expr(stmt.value)
            # Auto-convert non-strings for print
            lines.append(f"{self.indent()}print({val})")
        
        elif isinstance(stmt, PropertyAccess):
            # Property access is an expression, not a statement - skip or handle as needed
            # For standalone property access (rare), we just ignore it
            pass
        
        elif isinstance(stmt, IfStmt):
            cond = self.generate_expr(stmt.condition)
            lines.append(f"{self.indent()}if {cond}:")
            self.indent_level += 1
            for s in stmt.then_block:
                self.generate_statement(s, lines)
            self.indent_level -= 1
            
            for elif_cond, elif_block in stmt.elif_blocks:
                c = self.generate_expr(elif_cond)
                lines.append(f"{self.indent()}elif {c}:")
                self.indent_level += 1
                for s in elif_block:
                    self.generate_statement(s, lines)
                self.indent_level -= 1
            
            if stmt.else_block:
                lines.append(f"{self.indent()}else:")
                self.indent_level += 1
                for s in stmt.else_block:
                    self.generate_statement(s, lines)
                self.indent_level -= 1
        
        elif isinstance(stmt, LoopRange):
            count = self.generate_expr(stmt.count)
            lines.append(f"{self.indent()}for {stmt.var} in range({count}):")
            self.indent_level += 1
            for s in stmt.body:
                self.generate_statement(s, lines)
            self.indent_level -= 1
        
        elif isinstance(stmt, LoopForeach):
            lines.append(f"{self.indent()}for {stmt.var} in {stmt.collection}:")
            self.indent_level += 1
            for s in stmt.body:
                self.generate_statement(s, lines)
            self.indent_level -= 1
        
        elif isinstance(stmt, LoopWhile):
            cond = self.generate_expr(stmt.condition)
            lines.append(f"{self.indent()}while {cond}:")
            self.indent_level += 1
            for s in stmt.body:
                self.generate_statement(s, lines)
            self.indent_level -= 1
        
        elif isinstance(stmt, FunctionDef):
            params = ", ".join(stmt.params)
            lines.append(f"{self.indent()}def {stmt.name}({params}):")
            self.indent_level += 1
            for s in stmt.body:
                self.generate_statement(s, lines)
            self.indent_level -= 1
        
        elif isinstance(stmt, FunctionCall):
            args = ", ".join(self.generate_expr(a) for a in stmt.args)
            if stmt.assign_to:
                lines.append(f"{self.indent()}{stmt.assign_to} = {stmt.name}({args})")
            else:
                lines.append(f"{self.indent()}{stmt.name}({args})")
        
        elif isinstance(stmt, ReturnStmt):
            val = self.generate_expr(stmt.value)
            lines.append(f"{self.indent()}return {val}")
        
        elif isinstance(stmt, BreakStmt):
            lines.append(f"{self.indent()}break")
        
        elif isinstance(stmt, ExitStmt):
            lines.append(f"{self.indent()}exit()")
        
        elif isinstance(stmt, ListCreate):
            lines.append(f"{self.indent()}{stmt.target} = []")
        
        elif isinstance(stmt, ListAppend):
            val = self.generate_expr(stmt.value)
            lines.append(f"{self.indent()}{stmt.target}.append({val})")
        
        else:
            raise ValueError(f"Unknown statement type: {type(stmt)}")
    
    def generate_expr(self, expr: ASTNode) -> str:
        if isinstance(expr, Number):
            return str(expr.value)
        elif isinstance(expr, StringLit):
            escaped = expr.value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(expr, VarRef):
            return expr.name
        elif isinstance(expr, PropertyAccess):
            return f"{expr.obj}.{expr.prop}"
        elif isinstance(expr, BinaryOp):
            left = self.generate_expr(expr.left)
            right = self.generate_expr(expr.right)
            # Map E+ operators to Python
            op_map = {'and': 'and', 'or': 'or'}
            py_op = op_map.get(expr.op, expr.op)
            return f"({left} {py_op} {right})"
        else:
            raise ValueError(f"Unknown expression type: {type(expr)}")


# =============================================================================
# 5. COMPILER (Main Entry Point)
# =============================================================================

class EPlusCompiler:
    def compile(self, source: str) -> str:
        # Stage 1: Lexing
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Stage 2: Parsing
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Stage 3: Code Generation
        generator = CodeGenerator()
        python_code = generator.generate(ast)
        
        return python_code


# =============================================================================
# 6. TEST SUITE
# =============================================================================

def run_tests():
    compiler = EPlusCompiler()
    
    tests = [
        ("Simple Assignment", 
         "@age = (25)", 
         "age = 25"),
        
        ("Input/Output Canonical",
         '@user = input("Enter name")\nsay("Hello")',
         'user = int(input("Enter name"))\nprint("Hello")'),
        
        ("Input/Output Shorthand",
         '@user = < ("Enter name")\n> ("Hello")',
         'user = int(input("Enter name"))\nprint("Hello")'),
        
        # Note: Shorthand < must be in assignment context per spec
        # The test below shows the correct usage pattern
        
        ("Condition Chain",
         '''if (@age > 18) {
    say("Adult")
} else if (@age > 12) {
    say("Teen")
} else {
    say("Child")
}''',
         '''if (age > 18):
    print("Adult")
elif (age > 12):
    print("Teen")
else:
    print("Child")'''),
        
        ("Range Loop",
         '''repeat (@i, 10) {
    say(@i)
}''',
         '''for i in range(10):
    print(i)'''),
        
        ("Foreach Loop",
         '''repeat (@item, @fruits) {
    say(@item)
}''',
         '''for item in fruits:
    print(item)'''),
        
        ("While Loop",
         '''repeat while (@x > 0) {
    @x = (@x - 1)
}''',
         '''while (x > 0):
    x = (x - 1)'''),
        
        ("Function Definition & Call",
         '''function Add(@a, @b) {
    @result = (@a + @b)
    return(@result)
}
@answer = call Add(10, 20)''',
         '''def Add(a, b):
    result = (a + b)
    return result
answer = Add(10, 20)'''),
        
        ("List Operations",
         '''@items = list()
append(@items, "Apple")
append(@items, "Mango")''',
         '''items = []
items.append("Apple")
items.append("Mango")'''),
        
        ("Property Access in Expression",
         '''@color = @car.color''',
         '''color = car.color'''),
        
        ("Full Program",
         '''@user = input("Nama")
if (@user == "Admin") {
    say("Welcome Admin")
} else {
    say("Hello User")
}''',
         '''user = int(input("Nama"))
if (user == "Admin"):
    print("Welcome Admin")
else:
    print("Hello User")'''),
    ]
    
    print("=" * 70)
    print("E+ Compiler v4.0 — Test Suite")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for name, eplus_src, expected_py in tests:
        try:
            result = compiler.compile(eplus_src)
            result = result.strip()
            expected = expected_py.strip()
            
            if result == expected:
                print(f"✅ PASS: {name}")
                passed += 1
            else:
                print(f"❌ FAIL: {name}")
                print(f"   Expected:\n{expected}")
                print(f"   Got:\n{result}")
                failed += 1
        except Exception as e:
            print(f"❌ ERROR: {name} — {e}")
            failed += 1
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
