"""
E+ Lexer (Tokenizer)

This module implements the tokenizer for the E+ DSL.
It converts source code into a stream of tokens for parsing.
"""

from enum import Enum, auto
from typing import List, Optional
from dataclasses import dataclass


class TokenType(Enum):
    """Token types for E+ language."""
    
    # Literals
    NUMBER = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    
    # Identifiers & Variables
    IDENTIFIER = auto()
    VARIABLE = auto()  # Starts with @
    
    # Keywords
    INPUT = auto()
    SAY = auto()
    IF = auto()
    ELSE = auto()
    ELIF = auto()
    REPEAT = auto()
    WHILE = auto()
    FUNCTION = auto()
    CALL = auto()
    RETURN = auto()
    BREAK = auto()
    EXIT = auto()
    
    # Operators
    EQUALS = auto()        # =
    PLUS = auto()          # +
    MINUS = auto()         # -
    STAR = auto()          # *
    SLASH = auto()         # /
    PERCENT = auto()       # %
    
    # Comparison
    EQ = auto()            # ==
    NE = auto()            # !=
    LT = auto()            # <
    GT = auto()            # >
    LE = auto()            # <=
    GE = auto()            # >=
    
    # Delimiters
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    LBRACE = auto()        # {
    RBRACE = auto()        # }
    COMMA = auto()         # ,
    DOT = auto()           # .
    
    # Special
    NEWLINE = auto()
    EOF = auto()
    ILLEGAL = auto()


@dataclass
class Token:
    """Represents a single token."""
    type: TokenType
    value: any
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"


class LexerError(Exception):
    """Exception raised for lexer errors."""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Lexer error at line {line}, column {column}: {message}")


class Lexer:
    """Tokenizer for E+ language."""
    
    KEYWORDS = {
        'input': TokenType.INPUT,
        'say': TokenType.SAY,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'elif': TokenType.ELIF,
        'repeat': TokenType.REPEAT,
        'while': TokenType.WHILE,
        'function': TokenType.FUNCTION,
        'call': TokenType.CALL,
        'return': TokenType.RETURN,
        'break': TokenType.BREAK,
        'exit': TokenType.EXIT,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'null': TokenType.NULL,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def current_char(self) -> Optional[str]:
        """Get current character or None if at end."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek at character ahead without advancing."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """Advance position and return current character."""
        char = self.current_char()
        if char is not None:
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char
    
    def skip_whitespace(self):
        """Skip whitespace except newlines."""
        while self.current_char() is not None and self.current_char() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        """Skip single-line comments starting with #."""
        if self.current_char() == '#':
            while self.current_char() is not None and self.current_char() != '\n':
                self.advance()
    
    def read_string(self) -> Token:
        """Read a string literal enclosed in double quotes."""
        start_line = self.line
        start_col = self.column
        self.advance()  # Skip opening quote
        
        value = ""
        while self.current_char() is not None and self.current_char() != '"':
            if self.current_char() == '\\':
                self.advance()
                escape_char = self.current_char()
                if escape_char == 'n':
                    value += '\n'
                elif escape_char == 't':
                    value += '\t'
                elif escape_char == '\\':
                    value += '\\'
                elif escape_char == '"':
                    value += '"'
                else:
                    raise LexerError(f"Invalid escape sequence \\{escape_char}", self.line, self.column)
                self.advance()
            else:
                value += self.advance()
        
        if self.current_char() is None:
            raise LexerError("Unterminated string", start_line, start_col)
        
        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, value, start_line, start_col)
    
    def read_number(self) -> Token:
        """Read a number literal (integer or float)."""
        start_line = self.line
        start_col = self.column
        value = ""
        
        # Read integer part
        while self.current_char() is not None and self.current_char().isdigit():
            value += self.advance()
        
        # Check for decimal point
        if self.current_char() == '.' and self.peek_char() is not None and self.peek_char().isdigit():
            value += self.advance()  # Add the dot
            while self.current_char() is not None and self.current_char().isdigit():
                value += self.advance()
            return Token(TokenType.NUMBER, float(value), start_line, start_col)
        
        return Token(TokenType.NUMBER, int(value), start_line, start_col)
    
    def read_identifier_or_variable(self) -> Token:
        """Read an identifier or variable (starting with @)."""
        start_line = self.line
        start_col = self.column
        
        # Check if it's a variable (starts with @)
        is_variable = False
        if self.current_char() == '@':
            is_variable = True
            self.advance()
        
        value = ""
        while self.current_char() is not None and (self.current_char().isalnum() or self.current_char() == '_'):
            value += self.advance()
        
        if not value:
            raise LexerError("Expected identifier after '@'", start_line, start_col)
        
        if is_variable:
            return Token(TokenType.VARIABLE, value, start_line, start_col)
        
        # Check if it's a keyword
        if value.lower() in self.KEYWORDS:
            return Token(self.KEYWORDS[value.lower()], value, start_line, start_col)
        
        return Token(TokenType.IDENTIFIER, value, start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code."""
        while self.current_char() is not None:
            self.skip_whitespace()
            self.skip_comment()
            
            char = self.current_char()
            if char is None:
                break
            
            start_line = self.line
            start_col = self.column
            
            # Newline
            if char == '\n':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_col))
                continue
            
            # String
            if char == '"':
                self.tokens.append(self.read_string())
                continue
            
            # Number
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Variable or Identifier
            if char == '@' or char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier_or_variable())
                continue
            
            # Two-character operators
            next_char = self.peek_char()
            if char == '=' and next_char == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
                continue
            if char == '!' and next_char == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NE, '!=', start_line, start_col))
                continue
            if char == '<' and next_char == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.LE, '<=', start_line, start_col))
                continue
            if char == '>' and next_char == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.GE, '>=', start_line, start_col))
                continue
            
            # Single-character tokens
            single_char_tokens = {
                '=': TokenType.EQUALS,
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.STAR,
                '/': TokenType.SLASH,
                '%': TokenType.PERCENT,
                '<': TokenType.LT,
                '>': TokenType.GT,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                ',': TokenType.COMMA,
                '.': TokenType.DOT,
            }
            
            if char in single_char_tokens:
                self.advance()
                self.tokens.append(Token(single_char_tokens[char], char, start_line, start_col))
                continue
            
            raise LexerError(f"Unexpected character: '{char}'", start_line, start_col)
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens


def tokenize(source: str) -> List[Token]:
    """Convenience function to tokenize source code."""
    lexer = Lexer(source)
    return lexer.tokenize()
