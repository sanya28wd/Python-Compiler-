"""
Lexical Analyzer (Lexer) for the custom compiler
Performs lexical analysis on source code and generates tokens
"""

from tokens import Token, TokenType


class LexicalError(Exception):
    # Exception for lexical errors
    pass


class Lexer:
    # Lexical Analyzer - converts source code into tokens
    
    def __init__(self, source_code):
        """
        Initialize the lexer with source code.
        
        Args:
            source_code: The source program as a string
        """
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.errors = []
        
        # Keywords dictionary
        self.keywords = {
            'int': TokenType.KEYWORD_INT,
            'float': TokenType.KEYWORD_FLOAT,
            'if': TokenType.KEYWORD_IF,
            'else': TokenType.KEYWORD_ELSE,
            'while': TokenType.KEYWORD_WHILE,
            'print': TokenType.KEYWORD_PRINT,
        }
    
    def current_char(self):
        # Get current character
        if self.position >= len(self.source):
            return None
        return self.source[self.position]
    
    def peek_char(self, offset=1):
        # Peak at character ahed to use for two characters 
        pos = self.position + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self):
        # Move to next character
        if self.position < len(self.source):
            if self.source[self.position] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.position += 1
    
    def skip_whitespace(self):
        # Skip whitespace characters (except newlines)
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()   #to not skip newline
    
    def skip_newline(self):
        # Skip newline characters
        while self.current_char() and self.current_char() == '\n':
            self.advance()
    
    def read_number(self):
        # Read a number integer or float
        start_line = self.line
        start_column = self.column
        num_str = ''
        is_float = False
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if is_float:
                    # Multiple decimal points
                    self.errors.append(f"Lexical Error at Line {self.line}, Col {self.column}: Multiple decimal points in number")
                    break
                is_float = True
            num_str += self.current_char()
            self.advance()
        
        if is_float:
            return Token(TokenType.FLOAT, float(num_str), start_line, start_column)
        else:
            return Token(TokenType.INTEGER, int(num_str), start_line, start_column)
    
    def read_identifier(self):
        # Read identifier or keyword
        start_line = self.line
        start_column = self.column
        ident = ''
        
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            ident += self.current_char()
            self.advance()
        
        # Check if it's a keyword
        token_type = self.keywords.get(ident, TokenType.IDENTIFIER)
        return Token(token_type, ident, start_line, start_column)
    
    def tokenize(self):
        # Tokenize entire source code 
        while self.position < len(self.source):
            self.skip_whitespace()
            
            if self.position >= len(self.source):
                break
            
            current = self.current_char()
            line = self.line
            column = self.column
            
            # Newline
            if current == '\n':
                self.advance()
                continue
            
            # Numbers
            elif current.isdigit():
                self.tokens.append(self.read_number())
            
            # Identifiers and Keywords
            elif current.isalpha() or current == '_':
                self.tokens.append(self.read_identifier())
            
            # Operators and Delimiters
            elif current == '+':
                self.tokens.append(Token(TokenType.PLUS, '+', line, column))
                self.advance()
            
            elif current == '-':
                self.tokens.append(Token(TokenType.MINUS, '-', line, column))
                self.advance()
            
            elif current == '*':
                self.tokens.append(Token(TokenType.MULTIPLY, '*', line, column))
                self.advance()
            
            elif current == '/':
                self.tokens.append(Token(TokenType.DIVIDE, '/', line, column))
                self.advance()
            
            elif current == '%':
                self.tokens.append(Token(TokenType.MODULO, '%', line, column))
                self.advance()
            
            elif current == '=':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.EQ, '==', line, column))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, '=', line, column))
                    self.advance()
            
            elif current == '<':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.LE, '<=', line, column))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.LT, '<', line, column))
                    self.advance()
            
            elif current == '>':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.GE, '>=', line, column))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.GT, '>', line, column))
                    self.advance()
            
            elif current == '!':
                if self.peek_char() == '=':
                    self.tokens.append(Token(TokenType.NE, '!=', line, column))
                    self.advance()
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.NOT, '!', line, column))
                    self.advance()
            
            elif current == '&':
                if self.peek_char() == '&':
                    self.tokens.append(Token(TokenType.AND, '&&', line, column))
                    self.advance()
                    self.advance()
                else:
                    self.errors.append(f"Lexical Error at Line {line}, Col {column}: Unexpected character '&'")
                    self.advance()
            
            elif current == '|':
                if self.peek_char() == '|':
                    self.tokens.append(Token(TokenType.OR, '||', line, column))
                    self.advance()
                    self.advance()
                else:
                    self.errors.append(f"Lexical Error at Line {line}, Col {column}: Unexpected character '|'")
                    self.advance()
            
            elif current == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', line, column))
                self.advance()
            
            elif current == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', line, column))
                self.advance()
            
            elif current == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', line, column))
                self.advance()
            
            elif current == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', line, column))
                self.advance()
            
            elif current == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', line, column))
                self.advance()
            
            elif current == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', line, column))
                self.advance()
            
            else:
                self.errors.append(f"Lexical Error at Line {line}, Col {column}: Unexpected character '{current}'")
                self.advance()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        
        return self.tokens
    
    def print_tokens(self):
        # Print all tokens
        print("\n" + "="*80)
        print("LEXICAL ANALYSIS - TOKEN STREAM")
        print("="*80)
        
        if not self.tokens:
            print("No tokens generated")
            return
        
        print(f"{'Token Type':<20} {'Value':<20} {'Line':<8} {'Column':<8}")
        print("-"*80)
        
        for token in self.tokens:
            if token.type == TokenType.EOF:
                print(f"{'EOF':<20} {'<EOF>':<20} {token.line:<8} {token.column:<8}")
            else:
                print(f"{token.type:<20} {str(token.value):<20} {token.line:<8} {token.column:<8}")
        
        print("="*80)
    
    def print_errors(self):
        # Print all lexical errors
        if not self.errors:
            print("\nNo lexical errors found")
            return
        
        print("\n" + "="*80)
        print("LEXICAL ERRORS")
        print("="*80)
        for error in self.errors:
            print(f"  {error}")
        print("="*80)
    
    def has_errors(self):
        # Check if any errors
        return len(self.errors) > 0
