from typing import List, Optional
from compiler_core import Node, SymbolTable, Token, ParseError


class Parser:
    def __init__(self, tokens: List[Token], symbol_table: Optional[SymbolTable] = None):
        # assume lexer may or may not include EOF
        self.tokens = tokens + [Token("EOF", "$", 0, 0)]
        self.i = 0
        self.derivation_log = []
        # Use provided SymbolTable or create new one
        self.symbol_table = symbol_table if symbol_table else SymbolTable()

    def log_rule(self, rule):
        self.derivation_log.append(rule)

    def current(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        t = self.current()
        self.i += 1
        return t

    def expect(self, ttype: str) -> Token:
        tok = self.current()
        if tok.type != ttype:
            raise ParseError(
                f"Syntax error at line {tok.line}, col {tok.column}: "
                f"expected {ttype}, found {tok.type} ('{tok.value}')"
            )
        return self.advance()

    # -------------------- Semantic Helpers --------------------
    def _semantic_error(self, tok: Token, message: str):
        raise ParseError(f"Semantic Error at line {tok.line}, col {tok.column}: {message}")

    def _set_type(self, node: Node, inferred_type: str) -> Node:
        node.inferred_type = inferred_type
        return node

    def _is_numeric(self, t: str) -> bool:
        return t in ("INT", "FLOAT")

    def _assignment_compatible(self, lhs: str, rhs: str) -> bool:
        # Allow widening conversion INT -> FLOAT, disallow narrowing FLOAT -> INT
        return lhs == rhs or (lhs == "FLOAT" and rhs == "INT")

    def _binary_numeric_result_type(self, left_t: str, right_t: str, op_tok: Token) -> str:
        if not self._is_numeric(left_t) or not self._is_numeric(right_t):
            self._semantic_error(op_tok, f"Operator '{op_tok.value}' requires numeric operands, got {left_t} and {right_t}")

        if op_tok.type == "MOD":
            if left_t != "INT" or right_t != "INT":
                self._semantic_error(op_tok, "Operator '%' requires INT operands")
            return "INT"

        if op_tok.type == "DIV":
            return "FLOAT"

        return "FLOAT" if left_t == "FLOAT" or right_t == "FLOAT" else "INT"

    # Program -> StmtList EOF
    def parse_program(self):
        print("\n" + "="*80)
        print("SEMANTIC ANALYSIS - SYMBOL TABLE CONSTRUCTION")
        print("="*80)
        self.log_rule("Program -> StmtList")
        stmt_list_node = self.parse_stmt_list(stop_types={"EOF"})
        self.expect("EOF")
        
        # Print final symbol table state
        print("\n" + "="*80)
        print("FINAL SYMBOL TABLE STATE")
        print("="*80)
        self.symbol_table.print_current_state()
        print("="*80)
        
        return Node("Program", [stmt_list_node])

    # StmtList -> Stmt StmtList | ε
    def parse_stmt_list(self, stop_types: set):
        self.log_rule("StmtList -> Stmt StmtList")
        statements = []
        while self.current().type not in stop_types:
            statements.append(self.parse_stmt())
        
        if not statements:
            self.log_rule("StmtList -> ε")

        return Node("StmtList", statements)

    # Stmt -> Decl ; | Assign ; | IfStmt | WhileStmt | Block | PrintStmt ;
    def parse_stmt(self):
        t = self.current().type
        node = None

        if t in ("INT", "FLOAT"):
            self.log_rule("Stmt -> Decl ;")
            decl_node = self.parse_decl()
            semicolon = self.expect("SEMICOLON")
            node = Node("Stmt", [decl_node, semicolon])
        elif t == "ID":
            self.log_rule("Stmt -> Assign ;")
            assign_node = self.parse_assign()
            semicolon = self.expect("SEMICOLON")
            node = Node("Stmt", [assign_node, semicolon])
        elif t == "IF":
            self.log_rule("Stmt -> IfStmt")
            node = Node("Stmt", [self.parse_if()])
        elif t == "WHILE":
            self.log_rule("Stmt -> WhileStmt")
            node = Node("Stmt", [self.parse_while()])
        elif t == "LBRACE":
            self.log_rule("Stmt -> Block")
            node = Node("Stmt", [self.parse_block()])
        elif t == "PRINT":
            self.log_rule("Stmt -> PrintStmt ;")
            print_node = self.parse_print()
            semicolon = self.expect("SEMICOLON")
            node = Node("Stmt", [print_node, semicolon])
        else:
            tok = self.current()
            raise ParseError(
                f"Syntax error at line {tok.line}, col {tok.column}: "
                f"invalid statement start {tok.type} ('{tok.value}')"
            )
        return node

    # Decl -> Type ID
    def parse_decl(self):
        self.log_rule("Decl -> Type ID")
        type_node = self.parse_type()
        # Extract the type string (e.g., 'INT' or 'FLOAT') from the Type node
        type_str = type_node.children[0].type 
        id_token = self.expect("ID")
        
        # SEMANTIC ACTION: Register variable in symbol table
        try:
            self.symbol_table.insert(id_token.value, type_str)
            self.symbol_table.print_current_state()
        except Exception as e:
            raise ParseError(f"Semantic Error at line {id_token.line}: {str(e)}")
            
        return Node("Decl", [type_node, id_token])

    # Type -> INT | FLOAT
    def parse_type(self):
        if self.current().type == "INT":
            self.log_rule("Type -> INT")
            return Node("Type", [self.advance()])
        elif self.current().type == "FLOAT":
            self.log_rule("Type -> FLOAT")
            return Node("Type", [self.advance()])
        else:
            tok = self.current()
            raise ParseError(
                f"Syntax error at line {tok.line}, col {tok.column}: "
                f"type expected, found {tok.type}"
            )

    # Assign -> ID ASSIGN Expr
    def parse_assign(self):
        self.log_rule("Assign -> ID = Expr")
        id_token = self.expect("ID")
        
        # SEMANTIC ACTION: Check if variable exists before assigning
        symbol = self.symbol_table.lookup(id_token.value)
        if not symbol:
            raise ParseError(f"Semantic Error at line {id_token.line}: Undeclared variable '{id_token.value}'")
            
        assign_token = self.expect("ASSIGN")
        expr_node = self.parse_expr()

        lhs_type = symbol.type_.upper()
        rhs_type = getattr(expr_node, "inferred_type", None)
        if rhs_type is None:
            self._semantic_error(assign_token, "Unable to infer expression type in assignment")

        if not self._assignment_compatible(lhs_type, rhs_type):
            self._semantic_error(
                assign_token,
                f"Type mismatch in assignment to '{id_token.value}': cannot assign {rhs_type} to {lhs_type}"
            )

        return Node("Assign", [id_token, assign_token, expr_node])

    # IfStmt -> IF ( BoolExpr ) Stmt ElsePart
    def parse_if(self):
        self.log_rule("IfStmt -> if ( BoolExpr ) Stmt ElsePart")
        children = [self.expect("IF"), self.expect("LPAREN")]
        cond_node = self.parse_bool_expr()
        if getattr(cond_node, "inferred_type", None) != "BOOL":
            self._semantic_error(children[0], "Invalid boolean condition in if statement")
        children.append(cond_node)
        children.append(self.expect("RPAREN"))
        children.append(self.parse_stmt())
        
        if self.current().type == "ELSE":
            self.log_rule("ElsePart -> else Stmt")
            children.append(self.expect("ELSE"))
            children.append(self.parse_stmt())
        else:
            self.log_rule("ElsePart -> ε")

        return Node("IfStmt", children)

    # WhileStmt -> WHILE ( BoolExpr ) Stmt
    def parse_while(self):
        self.log_rule("WhileStmt -> while ( BoolExpr ) Stmt")
        children = [self.expect("WHILE"), self.expect("LPAREN")]
        cond_node = self.parse_bool_expr()
        if getattr(cond_node, "inferred_type", None) != "BOOL":
            self._semantic_error(children[0], "Invalid boolean condition in while statement")
        children.append(cond_node)
        children.append(self.expect("RPAREN"))
        children.append(self.parse_stmt())
        return Node("WhileStmt", children)

    # Block -> { StmtList }
    def parse_block(self):
        self.log_rule("Block -> { StmtList }")
        children = [self.expect("LBRACE")]
        
        # SEMANTIC ACTION: Enter a new scope for the block
        self.symbol_table.enter_scope()
        self.symbol_table.print_current_state()
        
        children.append(self.parse_stmt_list(stop_types={"RBRACE", "EOF"}))
        
        # SEMANTIC ACTION: Exit scope upon closing the block
        self.symbol_table.exit_scope()
        self.symbol_table.print_current_state()
        
        children.append(self.expect("RBRACE"))
        return Node("Block", children)

    # PrintStmt -> PRINT ( Expr )
    def parse_print(self):
        self.log_rule("PrintStmt -> print ( Expr )")
        children = [self.expect("PRINT"), self.expect("LPAREN")]
        children.append(self.parse_expr())
        children.append(self.expect("RPAREN"))
        return Node("PrintStmt", children)

    # Expr -> Term ((+|-) Term)*
    def parse_expr(self):
        self.log_rule("Expr -> Term ExprP")
        node = self.parse_term()
        while self.current().type in ("PLUS", "MINUS"):
            self.log_rule("ExprP -> + Term ExprP" if self.current().type == "PLUS" else "ExprP -> - Term ExprP")
            op = self.advance()
            right = self.parse_term()
            result_type = self._binary_numeric_result_type(
                getattr(node, "inferred_type", ""),
                getattr(right, "inferred_type", ""),
                op,
            )
            node = self._set_type(Node("Expr", [node, op, right]), result_type)
        self.log_rule("ExprP -> ε")
        if not hasattr(node, "inferred_type"):
            node = self._set_type(node, getattr(node, "inferred_type", "INT"))
        return node

    # Term -> Factor ((*|/|%) Factor)*
    def parse_term(self):
        self.log_rule("Term -> Factor TermP")
        node = self.parse_factor()
        while self.current().type in ("MUL", "DIV", "MOD"):
            self.log_rule("TermP -> * Factor TermP" if self.current().type == "MUL" else "TermP -> / Factor TermP" if self.current().type == "DIV" else "TermP -> % Factor TermP")
            op = self.advance()
            right = self.parse_factor()
            result_type = self._binary_numeric_result_type(
                getattr(node, "inferred_type", ""),
                getattr(right, "inferred_type", ""),
                op,
            )
            node = self._set_type(Node("Term", [node, op, right]), result_type)
        self.log_rule("TermP -> ε")
        if not hasattr(node, "inferred_type"):
            node = self._set_type(node, getattr(node, "inferred_type", "INT"))
        return node

    # Factor -> ID | INT_LIT | FLOAT_LIT | ( Expr )
    def parse_factor(self):
        t = self.current().type
        if t == "ID":
            self.log_rule("Factor -> ID")
            token = self.advance()
            
            # SEMANTIC ACTION: Verify variable is declared before use in expression
            symbol = self.symbol_table.lookup(token.value)
            if not symbol:
                raise ParseError(f"Semantic Error at line {token.line}: Undeclared variable '{token.value}'")
                
            return self._set_type(Node("Factor", [token]), symbol.type_.upper())
        elif t == "INT_LIT":
            self.log_rule("Factor -> INT_LIT")
            return self._set_type(Node("Factor", [self.advance()]), "INT")
        elif t == "FLOAT_LIT":
            self.log_rule("Factor -> FLOAT_LIT")
            return self._set_type(Node("Factor", [self.advance()]), "FLOAT")
        elif t == "LPAREN":
            self.log_rule("Factor -> ( Expr )")
            lparen = self.advance()
            expr_node = self.parse_expr()
            rparen = self.expect("RPAREN")
            return self._set_type(Node("Factor", [lparen, expr_node, rparen]), getattr(expr_node, "inferred_type", "INT"))
        else:
            tok = self.current()
            raise ParseError(
                f"Syntax error at line {tok.line}, col {tok.column}: "
                f"factor expected, found {tok.type} ('{tok.value}')"
            )

    # (Remaining Bool methods stay the same as they don't directly modify symbols)
    def parse_bool_expr(self):
        self.log_rule("BoolExpr -> BoolOr")
        node = self.parse_bool_or()
        return self._set_type(node, getattr(node, "inferred_type", "BOOL"))

    def parse_bool_or(self):
        self.log_rule("BoolOr -> BoolAnd BoolOrP")
        node = self.parse_bool_and()
        while self.current().type == "OR":
            self.log_rule("BoolOrP -> || BoolAnd BoolOrP")
            op = self.advance()
            right = self.parse_bool_and()
            if getattr(node, "inferred_type", None) != "BOOL" or getattr(right, "inferred_type", None) != "BOOL":
                self._semantic_error(op, "Operator '||' requires boolean operands")
            node = self._set_type(Node("BoolOr", [node, op, right]), "BOOL")
        self.log_rule("BoolOrP -> ε")
        if not hasattr(node, "inferred_type"):
            node = self._set_type(node, getattr(node, "inferred_type", "BOOL"))
        return node

    def parse_bool_and(self):
        self.log_rule("BoolAnd -> BoolNot BoolAndP")
        node = self.parse_bool_not()
        while self.current().type == "AND":
            self.log_rule("BoolAndP -> && BoolNot BoolAndP")
            op = self.advance()
            right = self.parse_bool_not()
            if getattr(node, "inferred_type", None) != "BOOL" or getattr(right, "inferred_type", None) != "BOOL":
                self._semantic_error(op, "Operator '&&' requires boolean operands")
            node = self._set_type(Node("BoolAnd", [node, op, right]), "BOOL")
        self.log_rule("BoolAndP -> ε")
        if not hasattr(node, "inferred_type"):
            node = self._set_type(node, getattr(node, "inferred_type", "BOOL"))
        return node

    def parse_bool_not(self):
        if self.current().type == "NOT":
            self.log_rule("BoolNot -> ! BoolNot")
            op = self.advance()
            child = self.parse_bool_not()
            if getattr(child, "inferred_type", None) != "BOOL":
                self._semantic_error(op, "Operator '!' requires a boolean operand")
            return self._set_type(Node("BoolNot", [op, child]), "BOOL")

        if self.current().type == "LPAREN":
            if self._looks_like_bool_parenthesized():
                self.log_rule("BoolNot -> ( BoolExpr )")
                lparen = self.expect("LPAREN")
                bool_expr = self.parse_bool_expr()
                rparen = self.expect("RPAREN")
                if getattr(bool_expr, "inferred_type", None) != "BOOL":
                    self._semantic_error(lparen, "Parenthesized boolean expression is not boolean")
                return self._set_type(Node("BoolNot", [lparen, bool_expr, rparen]), "BOOL")

        self.log_rule("BoolNot -> RelExpr")
        return self.parse_rel_expr()

    def parse_rel_expr(self):
        self.log_rule("RelExpr -> Expr RelTail")
        left_expr = self.parse_expr()
        if self.current().type in ("LT", "GT", "LE", "GE", "EQ", "NE"):
            self.log_rule("RelTail -> RelOp Expr")
            op = self.advance()
            right_expr = self.parse_expr()
            left_t = getattr(left_expr, "inferred_type", None)
            right_t = getattr(right_expr, "inferred_type", None)
            if not self._is_numeric(left_t) or not self._is_numeric(right_t):
                self._semantic_error(op, f"Relational operator '{op.value}' requires numeric operands, got {left_t} and {right_t}")
            return self._set_type(Node("RelExpr", [left_expr, op, right_expr]), "BOOL")
        else:
            self.log_rule("RelTail -> ε")
            # RelExpr without relational operator is arithmetic, not boolean.
            return self._set_type(Node("RelExpr", [left_expr]), getattr(left_expr, "inferred_type", "INT"))

    def _looks_like_bool_parenthesized(self) -> bool:
        depth = 0
        j = self.i
        while j < len(self.tokens):
            tt = self.tokens[j].type
            if tt == "LPAREN":
                depth += 1
            elif tt == "RPAREN":
                depth -= 1
                if depth == 0:
                    break
            elif depth >= 1 and tt in ("AND", "OR", "NOT", "LT", "GT", "LE", "GE", "EQ", "NE"):
                return True
            j += 1
        return False