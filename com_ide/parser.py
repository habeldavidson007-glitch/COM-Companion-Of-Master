"""
E+ Parser

This module implements a recursive descent parser for the E+ DSL.
It converts a stream of tokens into an Abstract Syntax Tree (AST).
"""

from typing import List, Optional, Any
from lexer import Token, TokenType, LexerError, tokenize
from eno_ast import ASTNode, Program, Assignment, Variable, Literal, Input, Output, BinaryOp, IfStatement, Loop, FunctionDef, FunctionCall, Return, Break, Exit, PropertyAccess


class ParseError(Exception):
    """Exception raised for parser errors."""
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"Parse error at line {token.line}, column {token.column}: {message}")


class Parser:
    """Recursive descent parser for E+ language."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self) -> Token:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.pos]
    
    def peek_token(self, offset: int = 1) -> Token:
        """Peek at token ahead without advancing."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """Advance to next token and return current."""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType, context: str = "") -> Token:
        """Expect a specific token type, raise error if not found."""
        token = self.current_token()
        if token.type != token_type:
            context_msg = f" while parsing {context}" if context else ""
            raise ParseError(
                f"Expected {token_type.name}{context_msg}, got {token.type.name}",
                token
            )
        return self.advance()
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token().type in token_types
    
    def skip_newlines(self):
        """Skip newline tokens."""
        while self.match(TokenType.NEWLINE):
            self.advance()
    
    def parse(self) -> Program:
        """Parse the entire program."""
        self.skip_newlines()
        statements = []
        
        while not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        return Program(statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        self.skip_newlines()
        
        token = self.current_token()
        
        if token.type == TokenType.VARIABLE:
            return self.parse_assignment_or_expression()
        elif token.type == TokenType.SAY:
            return self.parse_output()
        elif token.type == TokenType.IF:
            return self.parse_if_statement()
        elif token.type == TokenType.REPEAT:
            return self.parse_loop()
        elif token.type == TokenType.FUNCTION:
            return self.parse_function_def()
        elif token.type == TokenType.CALL:
            return self.parse_function_call()
        elif token.type == TokenType.RETURN:
            return self.parse_return()
        elif token.type == TokenType.BREAK:
            self.advance()
            return Break()
        elif token.type == TokenType.EXIT:
            self.advance()
            return Exit()
        elif token.type == TokenType.INPUT:
            # input() can be used in assignment or standalone
            return self.parse_input_statement()
        else:
            raise ParseError(f"Unexpected token: {token.type.name}", token)
    
    def parse_assignment_or_expression(self) -> ASTNode:
        """Parse variable assignment or standalone expression."""
        var_token = self.expect(TokenType.VARIABLE, "variable name")
        var_name = var_token.value
        
        if self.match(TokenType.EQUALS):
            self.advance()  # consume '='
            self.skip_newlines()
            
            # Parse the value expression
            value = self.parse_container_expression()
            return Assignment(var_name, value)
        else:
            # Standalone variable reference (unusual but valid)
            return Variable(var_name)
    
    def parse_container_expression(self) -> ASTNode:
        """Parse a container expression enclosed in parentheses."""
        if not self.match(TokenType.LPAREN):
            raise ParseError("Expected '(' for container expression", self.current_token())
        
        self.advance()  # consume '('
        self.skip_newlines()
        
        expr = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.RPAREN, "container closing")
        
        return expr
    
    def parse_expression(self) -> ASTNode:
        """Parse an expression (handles operator precedence)."""
        return self.parse_comparison()
    
    def parse_comparison(self) -> ASTNode:
        """Parse comparison expressions."""
        left = self.parse_additive()
        
        while self.match(TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op_token = self.advance()
            right = self.parse_additive()
            left = BinaryOp(left, op_token.value, right)
        
        return left
    
    def parse_additive(self) -> ASTNode:
        """Parse additive expressions (+, -)."""
        left = self.parse_multiplicative()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left, op_token.value, right)
        
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        """Parse multiplicative expressions (*, /, %)."""
        left = self.parse_primary()
        
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_token = self.advance()
            right = self.parse_primary()
            left = BinaryOp(left, op_token.value, right)
        
        return left
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expressions (literals, variables, function calls, property access)."""
        token = self.current_token()
        
        # Container expression
        if token.type == TokenType.LPAREN:
            self.advance()
            self.skip_newlines()
            expr = self.parse_expression()
            self.skip_newlines()
            self.expect(TokenType.RPAREN, "expression closing")
            return expr
        
        # Number literal
        if token.type == TokenType.NUMBER:
            self.advance()
            return Literal(token.value, "NUMBER")
        
        # String literal
        if token.type == TokenType.STRING:
            self.advance()
            return Literal(token.value, "STRING")
        
        # Boolean literals
        if token.type == TokenType.TRUE:
            self.advance()
            return Literal(True, "BOOL")
        if token.type == TokenType.FALSE:
            self.advance()
            return Literal(False, "BOOL")
        
        # Null literal
        if token.type == TokenType.NULL:
            self.advance()
            return Literal(None, "NULL")
        
        # Variable
        if token.type == TokenType.VARIABLE:
            self.advance()
            var_name = token.value
            
            # Check for property access
            if self.match(TokenType.DOT):
                self.advance()
                prop_token = self.expect(TokenType.IDENTIFIER, "property name")
                return PropertyAccess(var_name, prop_token.value)
            
            return Variable(var_name)
        
        # Input call
        if token.type == TokenType.INPUT:
            return self.parse_input_call()
        
        raise ParseError(f"Unexpected token in expression: {token.type.name}", token)
    
    def parse_input_call(self) -> Input:
        """Parse input() function call."""
        self.expect(TokenType.INPUT, "input keyword")
        self.expect(TokenType.LPAREN, "input arguments")
        self.skip_newlines()
        
        prompt = Literal("", "STRING")  # Default empty prompt
        if not self.match(TokenType.RPAREN):
            prompt = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.RPAREN, "input closing")
        
        return Input(prompt)
    
    def parse_input_statement(self) -> ASTNode:
        """Parse input statement (can be assignment or standalone)."""
        input_call = self.parse_input_call()
        
        # Check if it's part of an assignment (handled by parse_assignment_or_expression)
        return input_call
    
    def parse_output(self) -> Output:
        """Parse say() statement."""
        self.expect(TokenType.SAY, "say keyword")
        self.expect(TokenType.LPAREN, "say arguments")
        self.skip_newlines()
        
        value = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.RPAREN, "say closing")
        
        return Output(value)
    
    def parse_if_statement(self) -> IfStatement:
        """Parse if/elif/else statement."""
        self.expect(TokenType.IF, "if keyword")
        self.expect(TokenType.LPAREN, "if condition")
        self.skip_newlines()
        
        condition = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.RPAREN, "condition closing")
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "if block")
        
        then_block = self.parse_block()
        
        self.skip_newlines()
        self.expect(TokenType.RBRACE, "if block closing")
        
        # Parse elif branches
        elif_branches = []
        while self.match(TokenType.ELIF):
            self.advance()
            self.expect(TokenType.LPAREN, "elif condition")
            self.skip_newlines()
            
            elif_condition = self.parse_expression()
            
            self.skip_newlines()
            self.expect(TokenType.RPAREN, "elif condition closing")
            self.skip_newlines()
            self.expect(TokenType.LBRACE, "elif block")
            
            elif_block = self.parse_block()
            
            self.skip_newlines()
            self.expect(TokenType.RBRACE, "elif block closing")
            
            elif_branches.append((elif_condition, elif_block))
        
        # Parse else block
        else_block = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.skip_newlines()
            self.expect(TokenType.LBRACE, "else block")
            else_block = self.parse_block()
            self.skip_newlines()
            self.expect(TokenType.RBRACE, "else block closing")
        
        return IfStatement(condition, then_block, elif_branches, else_block)
    
    def parse_loop(self) -> Loop:
        """Parse repeat loop (range or while)."""
        self.expect(TokenType.REPEAT, "repeat keyword")
        
        if self.match(TokenType.WHILE):
            # While loop: repeat while (condition) { ... }
            self.advance()
            self.expect(TokenType.LPAREN, "while condition")
            self.skip_newlines()
            
            condition = self.parse_expression()
            
            self.skip_newlines()
            self.expect(TokenType.RPAREN, "while condition closing")
            self.skip_newlines()
            self.expect(TokenType.LBRACE, "loop body")
            
            body = self.parse_block()
            
            self.skip_newlines()
            self.expect(TokenType.RBRACE, "loop body closing")
            
            return Loop("WHILE", None, None, condition, body)
        else:
            # Range loop: repeat (@i, 10) { ... }
            self.expect(TokenType.LPAREN, "loop parameters")
            self.skip_newlines()
            
            # Get iterator variable
            iterator_token = self.expect(TokenType.VARIABLE, "iterator variable")
            iterator = iterator_token.value
            
            self.expect(TokenType.COMMA, "loop separator")
            self.skip_newlines()
            
            limit = self.parse_expression()
            
            self.skip_newlines()
            self.expect(TokenType.RPAREN, "loop parameters closing")
            self.skip_newlines()
            self.expect(TokenType.LBRACE, "loop body")
            
            body = self.parse_block()
            
            self.skip_newlines()
            self.expect(TokenType.RBRACE, "loop body closing")
            
            return Loop("RANGE", iterator, limit, None, body)
    
    def parse_block(self) -> List[ASTNode]:
        """Parse a block of statements."""
        statements = []
        self.skip_newlines()
        
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        return statements
    
    def parse_function_def(self) -> FunctionDef:
        """Parse function definition."""
        self.expect(TokenType.FUNCTION, "function keyword")
        
        name_token = self.expect(TokenType.IDENTIFIER, "function name")
        name = name_token.value
        
        self.expect(TokenType.LPAREN, "function parameters")
        self.skip_newlines()
        
        params = []
        if not self.match(TokenType.RPAREN):
            while True:
                param_token = self.expect(TokenType.VARIABLE, "parameter")
                params.append(param_token.value)
                
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
                self.skip_newlines()
        
        self.skip_newlines()
        self.expect(TokenType.RPAREN, "function parameters closing")
        self.skip_newlines()
        self.expect(TokenType.LBRACE, "function body")
        
        body = self.parse_block()
        
        self.skip_newlines()
        self.expect(TokenType.RBRACE, "function body closing")
        
        return FunctionDef(name, params, body)
    
    def parse_function_call(self) -> FunctionCall:
        """Parse function call with optional assignment."""
        self.expect(TokenType.CALL, "call keyword")
        
        name_token = self.expect(TokenType.IDENTIFIER, "function name")
        name = name_token.value
        
        self.expect(TokenType.LPAREN, "function arguments")
        self.skip_newlines()
        
        args = []
        if not self.match(TokenType.RPAREN):
            while True:
                arg = self.parse_expression()
                args.append(arg)
                
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
                self.skip_newlines()
        
        self.skip_newlines()
        self.expect(TokenType.RPAREN, "function arguments closing")
        
        return FunctionCall(name, args)
    
    def parse_return(self) -> Return:
        """Parse return statement."""
        self.expect(TokenType.RETURN, "return keyword")
        self.expect(TokenType.LPAREN, "return value")
        self.skip_newlines()
        
        value = self.parse_expression()
        
        self.skip_newlines()
        self.expect(TokenType.RPAREN, "return closing")
        
        return Return(value)


def parse(source: str) -> Program:
    """Convenience function to parse source code."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse()
