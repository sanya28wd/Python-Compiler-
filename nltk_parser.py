
import nltk
from nltk import CFG
from nltk.parse import EarleyChartParser

grammar_string = """
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

# Create a CFG object from the grammar string
grammar = CFG.fromstring(grammar_string)

parser = EarleyChartParser(grammar)

def parse_sentence(tokens):
    try:
        return parser.parse(tokens)
    except ValueError as e:
        print(f"Syntax Error: {e}")
        return []

