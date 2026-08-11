"""
Core Compiler Module - Consolidated compiler components
Combines tokens, symbol table, AST nodes, and parsing utilities
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
try:
    import nltk
    from nltk import CFG
    from nltk.parse import EarleyChartParser
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# ==================== TOKEN DEFINITIONS ====================

class TokenType:
    # Keywords
    INT = "INT"
    FLOAT = "FLOAT"
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    PRINT = "PRINT"
    
    # Identifiers and Literals
    ID = "ID"
    INT_LIT = "INT_LIT"
    FLOAT_LIT = "FLOAT_LIT"
    
    # Arithmetic Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    
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


class Token:
    """Represents a lexical token"""
    
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Token({self.type}, '{self.value}', Line {self.line}, Col {self.column})"
    
    def __repr__(self):
        return self.__str__()


# ==================== SYMBOL TABLE ====================

@dataclass
class SymbolInfo:
    """Information about a declared variable"""
    name: str
    type_: str
    scope_level: int
    memory_offset: int
    
    def __str__(self):
        return f"Symbol(name='{self.name}', type='{self.type_}', scope={self.scope_level}, offset={self.memory_offset})"


class SymbolTable:
    """Manages variable declarations and scope resolution"""
    
    def __init__(self):
        self.scopes: List[Dict[str, SymbolInfo]] = []
        self.scope_level = -1
        self.offset_stack: List[int] = []
        self.enter_scope()  # Initialize global scope
        
    def __str__(self):
        """Pretty print current symbol table state"""
        result = "\n" + "="*60 + "\n"
        result += "SYMBOL TABLE STATE\n"
        result += "="*60 + "\n"
        
        for i, scope in enumerate(self.scopes):
            scope_name = "Global" if i == 0 else f"Block {i}"
            result += f"\n{scope_name} (Level {i}):\n"
            if scope:
                result += f"{'Name':<15} {'Type':<10} {'Offset':<10}\n"
                result += "-"*40 + "\n"
                for name, info in scope.items():
                    result += f"{name:<15} {info.type_:<10} {info.memory_offset:<10}\n"
            else:
                result += "  (empty)\n"
        
        result += "="*60 + "\n"
        return result

    def enter_scope(self):
        """Enter a new scope level"""
        self.scope_level += 1
        self.scopes.append({})
        self.offset_stack.append(0)
        scope_name = "Global" if self.scope_level == 0 else f"Block {self.scope_level}"
        print(f"[SEMANTIC] Entering {scope_name} (Level {self.scope_level})")

    def exit_scope(self):
        """Exit current scope level"""
        if self.scope_level > 0:
            scope_name = f"Block {self.scope_level}"
            print(f"[SEMANTIC] Exiting {scope_name} (Level {self.scope_level})")
            print(f"[SEMANTIC] Removing {len(self.scopes[-1])} variable(s) from scope {self.scope_level}")
            self.scopes.pop()
            self.offset_stack.pop()
            self.scope_level -= 1
        else:
            print("[SEMANTIC] Cannot exit global scope")

    def insert(self, name: str, type_: str) -> SymbolInfo:
        """Insert a new variable declaration"""
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise Exception(f"Semantic Error: Variable '{name}' already declared in current scope (level {self.scope_level}).")
        
        offset = self.offset_stack[-1]
        size = 4 if type_.upper() == "INT" else 8
        
        info = SymbolInfo(name, type_, self.scope_level, offset)
        current_scope[name] = info
        self.offset_stack[-1] += size
        
        scope_name = "Global" if self.scope_level == 0 else f"Block {self.scope_level}"
        print(f"[SEMANTIC] INSERT: '{name}' | Type: {type_} | {scope_name} | Offset: {offset} | Size: {size} bytes")
        return info

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        """Look up a variable in the symbol table"""
        for i in range(len(self.scopes) - 1, -1, -1):
            scope = self.scopes[i]
            if name in scope:
                info = scope[name]
                scope_name = "Global" if info.scope_level == 0 else f"Block {info.scope_level}"
                print(f"[SEMANTIC] LOOKUP: Found '{name}' in {scope_name} (Level {info.scope_level}) at offset {info.memory_offset}")
                return info
        
        print(f"[SEMANTIC] LOOKUP: Variable '{name}' not found in any scope")
        return None
    
    def print_current_state(self):
        """Print detailed current state of symbol table"""
        print(self)


# ==================== AST NODES ====================

class Node:
    """Abstract Syntax Tree node"""
   
    def __init__(self, type, children=None):
        self.type = type
        self.children = children if children is not None else []

    def __repr__(self):
        return f"Node({self.type})"


def print_tree(node, prefix="", is_last=True):
    """Print the syntax tree in a human-readable format"""
    print(prefix + ("└── " if is_last else "├── ") + str(node.type))
    
    child_prefix = prefix + ("    " if is_last else "│   ")
    
    if not hasattr(node, 'children'):
        return

    for i, child in enumerate(node.children):
        is_child_last = (i == len(node.children) - 1)
        if isinstance(child, Node):
            print_tree(child, child_prefix, is_child_last)
        else:
            token_repr = f"{child.type} ('{child.value}')"
            print(child_prefix + ("└── " if is_child_last else "├── ") + token_repr)


# ==================== NLTK PARSER UTILITIES ====================

# Grammar string for NLTK parsing
GRAMMAR_STRING = """
    Program -> StmtList
    StmtList -> Stmt StmtList | Stmt

    Stmt -> Decl 'SEMICOLON'
    Stmt -> Assign 'SEMICOLON'
    Stmt -> IfStmt
    Stmt -> WhileStmt
    Stmt -> Block
    Stmt -> PrintStmt 'SEMICOLON'

    Decl -> Type 'ID'
    Type -> 'INT'
    Type -> 'FLOAT'

    Assign -> 'ID' 'ASSIGN' Expr

    IfStmt -> 'IF' 'LPAREN' BoolExpr 'RPAREN' Block 'ELSE' Block
    IfStmt -> 'IF' 'LPAREN' BoolExpr 'RPAREN' Block

    WhileStmt -> 'WHILE' 'LPAREN' BoolExpr 'RPAREN' Block

    Block -> 'LBRACE' StmtList 'RBRACE'

    PrintStmt -> 'PRINT' 'LPAREN' Expr 'RPAREN'

    Expr -> Expr 'PLUS' Term
    Expr -> Expr 'MINUS' Term
    Expr -> Term

    Term -> Term 'MUL' Factor
    Term -> Term 'DIV' Factor
    Term -> Term 'MOD' Factor
    Term -> Factor

    Factor -> 'ID'
    Factor -> 'INT_LIT'
    Factor -> 'FLOAT_LIT'
    Factor -> 'LPAREN' Expr 'RPAREN'

    BoolExpr -> BoolExpr 'OR' BoolAnd
    BoolExpr -> BoolAnd

    BoolAnd -> BoolAnd 'AND' BoolNot
    BoolAnd -> BoolNot

    BoolNot -> 'NOT' BoolNot
    BoolNot -> RelExpr
    BoolNot -> 'LPAREN' BoolExpr 'RPAREN'

    RelExpr -> Expr 'LT' Expr
    RelExpr -> Expr 'GT' Expr
    RelExpr -> Expr 'LE' Expr
    RelExpr -> Expr 'GE' Expr
    RelExpr -> Expr 'EQ' Expr
    RelExpr -> Expr 'NE' Expr
"""

# Create NLTK grammar and parser
if NLTK_AVAILABLE:
    try:
        nltk_grammar = CFG.fromstring(GRAMMAR_STRING)
        nltk_parser = EarleyChartParser(nltk_grammar)
    except:
        nltk_grammar = None
        nltk_parser = None
else:
    nltk_grammar = None
    nltk_parser = None


def parse_with_nltk(tokens):
    """Parse tokens using NLTK parser"""
    if not nltk_parser:
        return []
    
    try:
        return nltk_parser.parse(tokens)
    except ValueError as e:
        print(f"Syntax Error: {e}")
        return []


# ==================== COMPILER EXCEPTIONS ====================

class LexicalError(Exception):
    """Exception for lexical errors"""
    pass


class ParseError(Exception):
    """Exception for parsing errors"""
    pass


class SemanticError(Exception):
    """Exception for semantic errors"""
    pass
