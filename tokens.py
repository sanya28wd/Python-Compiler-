"""
Token class to represent lexical tokens in the compiler
"""

class TokenType:
    # Token definations
    
    # Keywords
    KEYWORD_INT = "KEYWORD_INT"
    KEYWORD_FLOAT = "KEYWORD_FLOAT"
    KEYWORD_IF = "KEYWORD_IF"
    KEYWORD_ELSE = "KEYWORD_ELSE"
    KEYWORD_WHILE = "KEYWORD_WHILE"
    KEYWORD_PRINT = "KEYWORD_PRINT"
    
    # Identifiers and Literals
    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    
    # Arithmetic Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"
    
    # Assignment
    ASSIGN = "ASSIGN"
    
    # Relational Operators
    LT = "LT"
    GT = "GT"
    LE = "LE"
    GE = "GE"
    EQ = "EQ"
    NE = "NE"
    
    # Boolean Operators
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    SEMICOLON = "SEMICOLON"
    COMMA = "COMMA"
    
    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"
    
    # Error
    UNKNOWN = "UNKNOWN"


class Token:
    # Represents a lexical token
    
    def __init__(self, token_type, value, line, column):
        """
        Initialize a token.
        
        Args:
            token_type: Type of the token (from TokenType)
            value: The actual value/lexeme
            line: Line number where token appears
            column: Column number where token appears
        """
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        # String representation of the token
        return f"Token({self.type}, '{self.value}', Line {self.line}, Col {self.column})"
    
    def __repr__(self):
        # Representation of the token
        return self.__str__()
