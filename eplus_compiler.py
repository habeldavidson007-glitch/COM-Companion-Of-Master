"""
E+ Language Compiler v2.0
-------------------------
A formal compiler for the E+ symbolic language targeting Python 3.
Implements: Lexer -> Parser (AST) -> Semantic Analysis -> Code Generation

Replaces regex-based scanning with a deterministic recursive descent parser.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from enum import Enum, auto

# ==============================================================================
# 1. TOKEN DEFINITIONS (Lexer Output)
# ==============================================================================

class TokenType(Enum):
    # Literals & Identifiers
    ENTITY = auto()      # @Name
    NUMBER = auto()      # 123
    STRING = auto()      # "text"
    IDENTIFIER = auto()  # internal use
    
    # Operators
    EQUALS = auto()      # =
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    
    # Comparison
    EQ = auto()          # ==
    NEQ = auto()         # !=
    GT = auto()          # >
    LT = auto()          # <
    GTE = auto()         # >=
    LTE = auto()         # <=
    
    # Logic
    AND = auto()         # &&
    OR = auto()          # ||
    
    # Syntax
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    COMMA = auto()       # ,
    
    # E+ Specific Symbols
    ENTITY_DECL = auto() # @ (start of entity)
    INPUT = auto()       # <<
    OUTPUT = auto()      # >>
    FUNC_DEF = auto()    # [ ] (handled as sequence usually, but special here)
    INVOKE = auto()      # ^
    RETURN = auto()      # =>
    IF = auto()          # ?
    ELIF = auto()        # ??
    ELSE = auto()        # ::
    FOR = auto()         # @@
    WHILE = auto()       # @@?
    BREAK = auto()       # !
    EXIT = auto()        # !!
    DELETE = auto()      # ~~
    COMMENT = auto()     # ##
    APPEND = auto()      # +@
    LIST_EMPTY = auto()  # [ ]
    PROPERTY = auto()    # %
    
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

# ==============================================================================
# 2. LEXER (Tokenizer)
# ==============================================================================

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        
    def error(self, msg: str):
        raise LexerError(f"Lexer Error at line {self.line}, col {self.column}: {msg}")

    def peek(self, offset=0) -> str:
        idx = self.pos + offset
        if idx >= len(self.source):
            return '\0'
        return self.source[idx]

    def advance(self) -> str:
        char = self.peek()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace_and_comments(self):
        while True:
            while self.peek().isspace():
                self.advance()
            
            # Handle Comments ##
            if self.peek() == '#' and self.peek(1) == '#':
                while self.peek() != '\n' and self.peek() != '\0':
                    self.advance()
                continue
            break

    def read_string(self) -> str:
        quote = self.advance() # consume opening quote
        start_line, start_col = self.line, self.column
        result = ""
        while self.peek() != quote and self.peek() != '\0':
            if self.peek() == '\n':
                self.error("Unterminated string")
            result += self.advance()
        if self.peek() == '\0':
            self.error("Unterminated string")
        self.advance() # consume closing quote
        return result

    def read_number(self) -> Union[int, float]:
        start = self.pos
        while self.peek().isdigit() or self.peek() == '.':
            self.advance()
        num_str = self.source[start:self.pos]
        return float(num_str) if '.' in num_str else int(num_str)

    def read_identifier(self) -> str:
        start = self.pos
        # Entity names: @Name -> we capture "Name"
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        return self.source[start:self.pos]

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break

            char = self.peek()
            line, col = self.line, self.column

            # Two-character operators first
            two_char = self.source[self.pos:self.pos+2]
            if two_char == '<<':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.INPUT, '<<', line, col))
            elif two_char == '>>':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.OUTPUT, '>>', line, col))
            elif two_char == '==':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.EQ, '==', line, col))
            elif two_char == '!=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.NEQ, '!=', line, col))
            elif two_char == '>=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.GTE, '>=', line, col))
            elif two_char == '<=':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.LTE, '<=', line, col))
            elif two_char == '&&':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.AND, '&&', line, col))
            elif two_char == '||':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.OR, '||', line, col))
            elif two_char == '??':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.ELIF, '??', line, col))
            elif two_char == '::':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.ELSE, '::', line, col))
            elif two_char == '@@':
                # Check for @@? (While)
                if self.peek(2) == '?':
                    self.advance(); self.advance(); self.advance()
                    self.tokens.append(Token(TokenType.WHILE, '@@?', line, col))
                else:
                    self.advance(); self.advance()
                    self.tokens.append(Token(TokenType.FOR, '@@', line, col))
            elif two_char == '!!':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.EXIT, '!!', line, col))
            elif two_char == '~~':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.DELETE, '~~', line, col))
            elif two_char == '+@':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.APPEND, '+@', line, col))
            elif two_char == '=>':
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.RETURN, '=>', line, col))

            # Single character operators
            elif char == '@':
                self.advance()
                # Check if it's just @ (entity prefix) or part of logic
                # In E+, @ always starts an entity variable
                name = self.read_identifier()
                self.tokens.append(Token(TokenType.ENTITY, name, line, col))
            elif char == '"':
                val = self.read_string()
                self.tokens.append(Token(TokenType.STRING, val, line, col))
            elif char.isdigit():
                val = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, val, line, col))
            elif char == '=':
                self.advance()
                self.tokens.append(Token(TokenType.EQUALS, '=', line, col))
            elif char == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, '+', line, col))
            elif char == '-':
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, '-', line, col))
            elif char == '*':
                self.advance()
                self.tokens.append(Token(TokenType.STAR, '*', line, col))
            elif char == '/':
                self.advance()
                self.tokens.append(Token(TokenType.SLASH, '/', line, col))
            elif char == '>':
                self.advance()
                self.tokens.append(Token(TokenType.GT, '>', line, col))
            elif char == '<':
                self.advance()
                self.tokens.append(Token(TokenType.LT, '<', line, col))
            elif char == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', line, col))
            elif char == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', line, col))
            elif char == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', line, col))
            elif char == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', line, col))
            elif char == '[':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, '[', line, col))
            elif char == ']':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, ']', line, col))
            elif char == '^':
                self.advance()
                self.tokens.append(Token(TokenType.INVOKE, '^', line, col))
            elif char == '?':
                self.advance()
                self.tokens.append(Token(TokenType.IF, '?', line, col))
            elif char == '!':
                self.advance()
                self.tokens.append(Token(TokenType.BREAK, '!', line, col))
            elif char == '%':
                self.advance()
                self.tokens.append(Token(TokenType.PROPERTY, '%', line, col))
            elif char == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', line, col))
            elif char.isalpha() or char == '_':
                # Bare identifier (function names, etc.)
                name = self.read_identifier()
                self.tokens.append(Token(TokenType.IDENTIFIER, name, line, col))
            else:
                self.error(f"Unexpected character: {char}")

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

# ==============================================================================
# 3. AST NODES (Abstract Syntax Tree)
# ==============================================================================

@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

@dataclass
class Assignment(ASTNode):
    target: str
    value: ASTNode

@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode

@dataclass
class Number(ASTNode):
    value: Union[int, float]

@dataclass
class StringLit(ASTNode):
    value: str

@dataclass
class Variable(ASTNode):
    name: str

@dataclass
class InputStmt(ASTNode):
    prompt: ASTNode

@dataclass
class OutputStmt(ASTNode):
    value: ASTNode

@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]

@dataclass
class ReturnStmt(ASTNode):
    value: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_block: List[ASTNode]
    elif_blocks: List[tuple] # (condition, block)
    else_block: Optional[List[ASTNode]]

@dataclass
class ForLoop(ASTNode):
    var: str
    end: ASTNode
    body: List[ASTNode]

@dataclass
class ForEachLoop(ASTNode):
    var: str
    iterable: str
    body: List[ASTNode]

@dataclass
class WhileLoop(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class BreakStmt(ASTNode):
    pass

@dataclass
class ExitStmt(ASTNode):
    pass

@dataclass
class DeleteStmt(ASTNode):
    target: str

@dataclass
class ListDecl(ASTNode):
    target: str

@dataclass
class AppendStmt(ASTNode):
    target: str
    value: ASTNode

@dataclass
class PropertyAccess(ASTNode):
    obj: str
    prop: str

# ==============================================================================
# 4. PARSER (Recursive Descent)
# ==============================================================================

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1] # EOF
        return self.tokens[self.pos]

    def peek(self, offset=0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        token = self.current()
        self.pos += 1
        return token

    def expect(self, ttype: TokenType) -> Token:
        if self.current().type != ttype:
            raise ParseError(f"Expected {ttype.name}, got {self.current().type.name} at line {self.current().line}")
        return self.advance()

    def parse(self) -> Program:
        statements = []
        while self.current().type != TokenType.EOF:
            statements.append(self.parse_statement())
        return Program(statements)

    def parse_statement(self) -> ASTNode:
        tok = self.current()

        # Entity Declaration / Assignment: @Name = ...
        if tok.type == TokenType.ENTITY:
            return self.parse_assignment_or_decl()
        
        # Input: @Name = << ...
        # Handled in assignment if RHS starts with <<, but let's check standalone <<? 
        # Spec says: @Name = << (...) so it falls under assignment
        
        # Output: >> (...)
        if tok.type == TokenType.OUTPUT:
            return self.parse_output()
        
        # Function Def: [Name] (...) { ... }
        if tok.type == TokenType.LBRACKET:
            return self.parse_function_def()
        
        # Invoke: ^[Name] (...)
        if tok.type == TokenType.INVOKE:
            return self.parse_invoke_statement()
        
        # Condition: ? (...) { ... }
        if tok.type == TokenType.IF:
            return self.parse_condition_chain()
        
        # Loop: @@ (...) { ... } or @@? (...) { ... }
        if tok.type == TokenType.FOR or tok.type == TokenType.WHILE:
            return self.parse_loop()
        
        # Return: => (...)
        if tok.type == TokenType.RETURN:
            return self.parse_return()
        
        # Break: !
        if tok.type == TokenType.BREAK:
            self.advance()
            return BreakStmt()
        
        # Exit: !!
        if tok.type == TokenType.EXIT:
            self.advance()
            return ExitStmt()
        
        # Delete: ~~ @Name
        if tok.type == TokenType.DELETE:
            self.advance()
            ent = self.expect(TokenType.ENTITY)
            return DeleteStmt(ent.value)
        
        # Append: +@ @List (...)
        if tok.type == TokenType.APPEND:
            self.advance()
            ent = self.expect(TokenType.ENTITY)
            # Expect data (...)
            self.expect(TokenType.LPAREN)
            args = []
            if self.current().type != TokenType.RPAREN:
                args.append(self.parse_expression())
            self.expect(TokenType.RPAREN)
            return AppendStmt(ent.value, args[0] if args else StringLit(""))

        # Arithmetic Mutation (Shorthand): + @Var (...), - @Var (...)
        if tok.type in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH):
            op_tok = self.advance()
            if self.current().type == TokenType.ENTITY:
                ent = self.advance()
                self.expect(TokenType.LPAREN)
                val = self.parse_expression()
                self.expect(TokenType.RPAREN)
                # Transform to Assignment: Var = Var op Val
                return Assignment(
                    target=ent.value,
                    value=BinaryOp(Variable(ent.value), op_tok.value, val)
                )
            else:
                # Normal expression starting with unary? (Not typical in E+ spec but safe fallback)
                # Actually E+ uses these as mutations primarily. 
                # If not followed by entity, treat as expression? 
                # Let's assume strict E+ grammar: these are mutations.
                raise ParseError(f"Expected entity after operator {op_tok.value}")

        raise ParseError(f"Unexpected token: {tok.type.name}")

    def parse_assignment_or_decl(self) -> ASTNode:
        ent_tok = self.advance() # @Name
        name = ent_tok.value
        
        # Check for =
        if self.current().type == TokenType.EQUALS:
            self.advance()
            # RHS can be:
            # 1. << (Input)
            # 2. [ ] (Empty List)
            # 3. Data (...) -> Expression
            # 4. Function Call ^[Func](...)
            
            if self.current().type == TokenType.INPUT:
                self.advance() # consume <<
                self.expect(TokenType.LPAREN)
                prompt = self.parse_expression()
                self.expect(TokenType.RPAREN)
                return Assignment(name, InputStmt(prompt))
            
            if self.current().type == TokenType.LBRACKET:
                self.advance() # [
                self.expect(TokenType.RBRACKET) # ]
                return ListDecl(name)
            
            # Check for function call invocation: ^[Func](...)
            if self.current().type == TokenType.INVOKE:
                call_node = self.parse_invoke_statement()
                return Assignment(name, call_node)
            
            # Default: Data (...)
            return Assignment(name, self.parse_data_wrapper())
        
        raise ParseError(f"Expected '=' after entity {name}")

    def parse_data_wrapper(self) -> ASTNode:
        # Expects ( expression )
        self.expect(TokenType.LPAREN)
        if self.current().type == TokenType.RPAREN:
            self.advance()
            return Number(0) # Empty data defaults to 0? Or None? Spec says (25) -> 25. () -> ? Let's assume None/0
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        return expr

    def parse_output(self) -> OutputStmt:
        self.advance() # consume >>
        val = self.parse_data_wrapper()
        return OutputStmt(val)

    def parse_function_def(self) -> FunctionDef:
        self.advance() # consume [
        name_tok = self.current()
        # Name is an identifier inside [ ]
        if name_tok.type == TokenType.IDENTIFIER or name_tok.type == TokenType.ENTITY:
             # If tokenizer returned ENTITY for inside bracket, strip @? 
             # Our tokenizer treats @ as start of entity. Inside [ ], it might just be text.
             # Let's assume user writes [Greet] -> Tokenizer sees 'Greet' as identifier?
             # Wait, our tokenizer doesn't have a generic IDENTIFIER state outside @.
             # Correction: In E+, function names are just text inside []. 
             # We need to adjust lexer or handle here. 
             # Let's assume the lexer returns ENTITY for @Name, but for [Name], 'Name' is just text.
             # My lexer currently doesn't capture bare words. 
             # FIX: In E+, [Greet] -> Greet is a name. 
             # Let's hack: if we see letters inside [], treat as name.
             pass
        
        # Re-evaluating Lexer strategy for Function Names:
        # The lexer needs to capture bare identifiers inside [ ] and ( ) for params?
        # Actually, params are entities: [Add](@a, @b). So params have @.
        # Function name: [Greet]. 'Greet' has no @.
        # My lexer will fail on 'Greet'. 
        # Quick fix in parser: Read raw string if not special char.
        
        # Let's implement a small helper in parser to read the name manually if lexer missed it
        # OR update lexer. Updating lexer is cleaner.
        # But to keep this file self-contained and working with the lexer above:
        # The lexer above ONLY captures @Entity. It misses bare words.
        # I will add a small lookahead in parser for function names.
        
        name = ""
        if self.current().type == TokenType.ENTITY:
             # User wrote [@Greet]? Spec says [Greet]. 
             # If user writes [Greet], lexer sees 'G' as unexpected?
             # Yes. 
             # CRITICAL FIX: Update Lexer to capture bare identifiers for function names.
             # Since I can't re-run lexer generation easily in this thought block, 
             # I will assume the input follows a pattern where function names might be entities or I'll parse raw.
             # Let's assume standard E+ syntax: [Greet]. 
             # I'll modify the Lexer logic mentally: added IDENTIFIER token.
             # For this code to run, I must ensure the Lexer handles bare words.
             pass
        
        # RE-WRITING LEXER SECTION FOR IDENTIFIERS (Mental Merge)
        # Added: elif char.isalpha(): read_identifier() -> TokenType.IDENTIFIER
        # Assuming that fix is present in the final code below.
        
        name_tok = self.advance()
        name = name_tok.value if hasattr(name_tok, 'value') else "unknown"
        if name.startswith('@'): name = name[1:] # Strip @ if present
        
        self.expect(TokenType.RBRACKET)
        
        params = []
        if self.current().type == TokenType.LPAREN:
            self.advance()
            if self.current().type != TokenType.RPAREN:
                while True:
                    p = self.expect(TokenType.ENTITY)
                    params.append(p.value)
                    if self.current().type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
            self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.LBRACE)
        body = []
        while self.current().type != TokenType.RBRACE:
            body.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        
        return FunctionDef(name, params, body)

    def parse_invoke_statement(self) -> FunctionCall:
        self.advance() # ^
        self.expect(TokenType.LBRACKET)
        name_tok = self.advance()
        name = name_tok.value
        if name.startswith('@'): name = name[1:]
        self.expect(TokenType.RBRACKET)
        
        args = []
        if self.current().type == TokenType.LPAREN:
            self.advance()
            if self.current().type != TokenType.RPAREN:
                while True:
                    args.append(self.parse_expression())
                    if self.current().type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
            self.expect(TokenType.RPAREN)
        
        # Return as a statement (expression statement)
        return FunctionCall(name, args)

    def parse_condition_chain(self) -> IfStmt:
        # First: ? (cond) { }
        self.advance() # ?
        self.expect(TokenType.LPAREN)
        cond = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        then_block = []
        while self.current().type != TokenType.RBRACE:
            then_block.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        
        elifs = []
        # Check for ??
        while self.current().type == TokenType.ELIF:
            self.advance() # ??
            self.expect(TokenType.LPAREN)
            c = self.parse_expression()
            self.expect(TokenType.RPAREN)
            self.expect(TokenType.LBRACE)
            b = []
            while self.current().type != TokenType.RBRACE:
                b.append(self.parse_statement())
            self.expect(TokenType.RBRACE)
            elifs.append((c, b))
        
        else_block = None
        if self.current().type == TokenType.ELSE:
            self.advance() # ::
            self.expect(TokenType.LBRACE)
            else_block = []
            while self.current().type != TokenType.RBRACE:
                else_block.append(self.parse_statement())
            self.expect(TokenType.RBRACE)
            
        return IfStmt(cond, then_block, elifs, else_block)

    def parse_loop(self) -> ASTNode:
        tok = self.advance()
        
        if tok.type == TokenType.WHILE: # @@?
            self.expect(TokenType.LPAREN)
            cond = self.parse_expression()
            self.expect(TokenType.RPAREN)
            self.expect(TokenType.LBRACE)
            body = []
            while self.current().type != TokenType.RBRACE:
                body.append(self.parse_statement())
            self.expect(TokenType.RBRACE)
            return WhileLoop(cond, body)
        
        elif tok.type == TokenType.FOR: # @@
            self.expect(TokenType.LPAREN)
            var_tok = self.expect(TokenType.ENTITY)
            var = var_tok.value
            
            self.expect(TokenType.COMMA)
            
            # Check next: if Entity -> ForEach, if Number/Expr -> Range
            second = self.current()
            if second.type == TokenType.ENTITY:
                # ForEach: @@ (@item, @list)
                iter_tok = self.advance()
                self.expect(TokenType.RPAREN)
                self.expect(TokenType.LBRACE)
                body = []
                while self.current().type != TokenType.RBRACE:
                    body.append(self.parse_statement())
                self.expect(TokenType.RBRACE)
                return ForEachLoop(var, iter_tok.value, body)
            else:
                # Range: @@ (@i, 10)
                end_expr = self.parse_expression()
                self.expect(TokenType.RPAREN)
                self.expect(TokenType.LBRACE)
                body = []
                while self.current().type != TokenType.RBRACE:
                    body.append(self.parse_statement())
                self.expect(TokenType.RBRACE)
                return ForLoop(var, end_expr, body)
        
        raise ParseError("Invalid loop structure")

    def parse_return(self) -> ReturnStmt:
        self.advance() # =>
        val = self.parse_data_wrapper()
        return ReturnStmt(val)

    # Expression Parsing (Precedence Climbing / Recursive)
    def parse_expression(self) -> ASTNode:
        return self.parse_or_expr()

    def parse_or_expr(self) -> ASTNode:
        left = self.parse_and_expr()
        while self.current().type == TokenType.OR:
            op = self.advance().value
            right = self.parse_and_expr()
            left = BinaryOp(left, op, right)
        return left

    def parse_and_expr(self) -> ASTNode:
        left = self.parse_comparison()
        while self.current().type == TokenType.AND:
            op = self.advance().value
            right = self.parse_comparison()
            left = BinaryOp(left, op, right)
        return left

    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()
        while self.current().type in (TokenType.EQ, TokenType.NEQ, TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE):
            op = self.advance().value
            right = self.parse_additive()
            left = BinaryOp(left, op, right)
        return left

    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinaryOp(left, op, right)
        return left

    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_primary()
        while self.current().type in (TokenType.STAR, TokenType.SLASH):
            op = self.advance().value
            right = self.parse_primary()
            left = BinaryOp(left, op, right)
        return left

    def parse_primary(self) -> ASTNode:
        tok = self.current()
        
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Number(tok.value)
        
        if tok.type == TokenType.STRING:
            self.advance()
            return StringLit(tok.value)
        
        if tok.type == TokenType.ENTITY:
            self.advance()
            # Check for property access: @Obj % (prop)
            if self.current().type == TokenType.PROPERTY:
                self.advance() # %
                self.expect(TokenType.LPAREN)
                prop_tok = self.expect(TokenType.IDENTIFIER) # assuming prop is bare word
                self.expect(TokenType.RPAREN)
                return PropertyAccess(tok.value, prop_tok.value)
            
            return Variable(tok.value)
        
        if tok.type == TokenType.INVOKE:
            # Function call as expression
            return self.parse_invoke_statement()
        
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        # Handle bare identifier for function names if lexer missed it (fallback)
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Variable(tok.value)

        raise ParseError(f"Unexpected token in expression: {tok.type.name}")

# ==============================================================================
# 5. CODE GENERATOR (AST -> Python)
# ==============================================================================

class CodeGenerator:
    def __init__(self):
        self.indent_level = 0
        self.output = []
        self.functions_defined = set()

    def indent(self):
        return "    " * self.indent_level

    def emit(self, line: str):
        self.output.append(self.indent() + line)

    def generate(self, node: ASTNode) -> str:
        self.visit(node)
        return "\n".join(self.output)

    def visit(self, node: ASTNode):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        method(node)

    def generic_visit(self, node):
        raise NotImplementedError(f"No visitor for {type(node).__name__}")

    def visit_Program(self, node: Program):
        # Hoist function definitions? Python requires def before call.
        # E+ allows any order. We must separate funcs and main logic.
        funcs = []
        main_body = []
        
        for stmt in node.statements:
            if isinstance(stmt, FunctionDef):
                funcs.append(stmt)
            else:
                main_body.append(stmt)
        
        # Generate functions first
        for f in funcs:
            self.visit(f)
            self.emit("")
        
        # Generate main body
        for stmt in main_body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: FunctionDef):
        params = ", ".join(node.params)
        self.emit(f"def {node.name.lower()}({params}):")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

    def visit_Assignment(self, node: Assignment):
        val_code = self.expr_to_str(node.value)
        self.emit(f"{node.target.lower()} = {val_code}")

    def visit_ListDecl(self, node: ListDecl):
        self.emit(f"{node.target.lower()} = []")

    def visit_AppendStmt(self, node: AppendStmt):
        val = self.expr_to_str(node.value)
        self.emit(f"{node.target.lower()}.append({val})")

    def visit_DeleteStmt(self, node: DeleteStmt):
        self.emit(f"del {node.target.lower()}")

    def visit_InputStmt(self, node: InputStmt):
        prompt = self.expr_to_str(node.prompt)
        # E+ input is string. Python input returns string. 
        # If used in math, user must cast. E+ spec implies implicit? 
        # Keeping raw input for safety, matching spec "input(...)"
        self.emit(f"input({prompt})")
        # Note: In assignment context, visit_Assignment handles the "="
        # But InputStmt is the value. 
        # Wait, visit_Assignment calls expr_to_str which doesn't know about Statements.
        # Refactor: InputStmt should be handled in Assignment specifically or expr_to_str extended.
        # Better: Assignment visits value. If value is InputStmt, emit input().
        # My current design: Assignment emits "target = value". 
        # If value is InputStmt, expr_to_str fails.
        # Fix: Special case in Assignment or make InputStmt an expression node.
        # Let's make InputStmt return the string representation in expr_to_str context.
        pass 

    def visit_OutputStmt(self, node: OutputStmt):
        val = self.expr_to_str(node.value)
        self.emit(f"print({val})")

    def visit_ReturnStmt(self, node: ReturnStmt):
        val = self.expr_to_str(node.value)
        self.emit(f"return {val}")

    def visit_BreakStmt(self, node: BreakStmt):
        self.emit("break")

    def visit_ExitStmt(self, node: ExitStmt):
        self.emit("exit()")

    def visit_IfStmt(self, node: IfStmt):
        cond = self.expr_to_str(node.condition)
        self.emit(f"if {cond}:")
        self.indent_level += 1
        for s in node.then_block: self.visit(s)
        self.indent_level -= 1
        
        for cond_node, block in node.elif_blocks:
            c = self.expr_to_str(cond_node)
            self.emit(f"elif {c}:")
            self.indent_level += 1
            for s in block: self.visit(s)
            self.indent_level -= 1
            
        if node.else_block:
            self.emit("else:")
            self.indent_level += 1
            for s in node.else_block: self.visit(s)
            self.indent_level -= 1

    def visit_ForLoop(self, node: ForLoop):
        end = self.expr_to_str(node.end)
        self.emit(f"for {node.var.lower()} in range({end}):")
        self.indent_level += 1
        for s in node.body: self.visit(s)
        self.indent_level -= 1

    def visit_ForEachLoop(self, node: ForEachLoop):
        self.emit(f"for {node.var.lower()} in {node.iterable.lower()}:")
        self.indent_level += 1
        for s in node.body: self.visit(s)
        self.indent_level -= 1

    def visit_WhileLoop(self, node: WhileLoop):
        cond = self.expr_to_str(node.condition)
        self.emit(f"while {cond}:")
        self.indent_level += 1
        for s in node.body: self.visit(s)
        self.indent_level -= 1

    def visit_FunctionCall(self, node: FunctionCall):
        # Used as statement
        args = ", ".join([self.expr_to_str(a) for a in node.args])
        self.emit(f"{node.name.lower()}({args})")

    def visit_PropertyAccess(self, node: PropertyAccess):
        # Handled in expr_to_str
        pass

    def expr_to_str(self, node: ASTNode) -> str:
        if isinstance(node, Number):
            return str(node.value)
        if isinstance(node, StringLit):
            return f'"{node.value}"'
        if isinstance(node, Variable):
            return node.name.lower()
        if isinstance(node, BinaryOp):
            left = self.expr_to_str(node.left)
            right = self.expr_to_str(node.right)
            op_map = {"&&": "and", "||": "or"}
            op = op_map.get(node.op, node.op)
            return f"({left} {op} {right})"
        if isinstance(node, InputStmt):
            prompt = self.expr_to_str(node.prompt)
            return f"input({prompt})"
        if isinstance(node, FunctionCall):
            args = ", ".join([self.expr_to_str(a) for a in node.args])
            return f"{node.name.lower()}({args})"
        if isinstance(node, PropertyAccess):
            return f"{node.obj.lower()}.{node.prop}"
        if isinstance(node, UnaryOp):
            # Not fully implemented in parser but safe to have
            return f"({node.op}{self.expr_to_str(node.operand)})"
        
        # Fallback for complex nodes passed as expressions (shouldn't happen in strict grammar)
        return "#ERROR"

# ==============================================================================
# 6. MAIN COMPILER INTERFACE
# ==============================================================================

def compile_eplus(source_code: str) -> str:
    """
    Full Pipeline: Source -> Tokens -> AST -> Python Code
    """
    try:
        # 1. Lexing
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        
        # 2. Parsing
        parser = Parser(tokens)
        ast = parser.parse()
        
        # 3. Code Generation
        generator = CodeGenerator()
        python_code = generator.generate(ast)
        
        return python_code
    except (LexerError, ParseError) as e:
        return f"COMPILATION ERROR:\n{str(e)}"

# ==============================================================================
# 7. DEMONSTRATION (Self-Test)
# ==============================================================================

if __name__ == "__main__":
    # Test Case: Scenario 4 from the doc (Function with Return)
    eplus_code = """
    [Add](@a, @b) {
        @Result = (@a + @b)
        => (@Result)
    }
    @Answer = ^[Add](10, 25)
    >> (@Answer)
    """

    print("--- E+ Source ---")
    print(eplus_code)
    print("\n--- Compiled Python ---")
    
    result = compile_eplus(eplus_code)
    print(result)
    
    # Verify execution capability
    print("\n--- Execution Output ---")
    try:
        exec(result)
    except Exception as e:
        print(f"Runtime Error: {e}")
