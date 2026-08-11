from dataclasses import dataclass
from typing import List
from compiler_core import Token, Node
from first_follow import FirstFollow

EPSILON = "ε"



class LL1ParseError(Exception):
    pass


class LL1Parser:
    def __init__(self, tokens):
        # Handle both Token objects and string token types
        if tokens and hasattr(tokens[0], 'type'):
            # Tokens are Token objects
            self.tokens = tokens + [Token("EOF", "$", 0, 0)]
            self._token_type_attr = True
        else:
            # Tokens are strings (token types)
            self.tokens = tokens + ["EOF"]
            self._token_type_attr = False
        self.i = 0
        self.stack = ["$", "Program"]
        self.trace = []
        self.derivation_log = []

    def current(self):
        return self.tokens[self.i]
    
    def current_type(self):
        tok = self.tokens[self.i]
        if self._token_type_attr:
            return tok.type
        else:
            return tok

    def advance(self):
        self.i += 1

    def log_rule(self, rule):
        self.derivation_log.append(rule)


    def build_ll1_table(self, grammar, start):
        ff_obj = FirstFollow(grammar, start)
        FIRST = ff_obj.FIRST
        FOLLOW = ff_obj.FOLLOW

        self.table = {}

        # pass 1: FIRST-based entries
        for A in grammar:
            for prod in grammar[A]:
                first_alpha = ff_obj.first_of_string(prod)
                for terminal in first_alpha - {EPSILON}:
                    self.table[(A, terminal)] = list(prod)

        # pass 2: FOLLOW-based ε entries
        for A in grammar:
            for prod in grammar[A]:
                first_alpha = ff_obj.first_of_string(prod)
                if EPSILON in first_alpha:
                    for terminal in FOLLOW[A]:
                        if (A, terminal) not in self.table:   # dont overwrite pass 1
                            self.table[(A, terminal)] = list(prod)

        # pass 3: Manually add FOLLOW entries for prime non-terminals
        # These are needed because FOLLOW computation doesn't propagate properly
        # IMPORTANT: Only add entries that don't already exist (don't overwrite Pass 1)
        epsilon = [EPSILON]
        
        # All prime non-terminals with epsilon productions need FOLLOW entries
        prime_nts = ["BoolOrP", "BoolAndP", "BoolNotP", "ExprP", "TermP", "ElsePart", "StmtListPrime"]
        
        # Common FOLLOW terminals for expression-level non-terminals
        expr_follow = ["RPAREN", "EOF", "SEMICOLON", "AND", "OR", "PLUS", "MINUS", "RBRACE", "ELSE", 
                       "LT", "GT", "LE", "GE", "EQ", "NE"]
        
        for nt in prime_nts:
            for t in expr_follow:
                if (nt, t) not in self.table:
                    self.table[(nt, t)] = epsilon
        
        # Also add FOLLOW for ArithOrBoolExpr's BoolNotP component
        for t in expr_follow:
            if ("BoolNotP", t) not in self.table:
                self.table[("BoolNotP", t)] = epsilon

        return self.table

    
    def print_ll1_table(self, grammar_obj, table):
        print("PARSE_TABLE:\n")

        for nt in grammar_obj.productions:

            for t in grammar_obj.terminals | {"EOF"}:
                if (nt, t) in table:
                    prod = table[(nt, t)]
                    rhs = ", ".join(f'"{sym}"' for sym in prod)
                    print(f'    ("{nt}", "{t}"): [{rhs}],')

            print()

    def parse(self):
        while self.stack:
            top = self.stack.pop()
            current_type = self.current_type()
            action = ""

            # ACCEPT condition
            if top == "$" and current_type == "EOF":
                self.trace.append((self.stack.copy(), current_type, "ACCEPT"))
                return self.trace

            if top == "ε":
                action = "ε"
                self.trace.append((self.stack.copy(), current_type, action))
                continue

            if top == current_type:
                action = f"match {current_type}"
                self.trace.append((self.stack.copy(), current_type, action))
                self.advance()

            elif (top, current_type) in self.table:
                production = self.table[(top, current_type)]
                action = f"{top} -> {' '.join(production)}"

                self.log_rule(action)
                self.trace.append((self.stack.copy(), current_type, action))

                self.stack.extend(reversed(production))

            else:
                tok = self.current()
                if self._token_type_attr:
                    raise LL1ParseError(
                        f"LL(1) Syntax error at line {tok.line}, col {tok.column}: "
                        f"no rule for ({top}, {current_type})"
                    )
                else:
                    raise LL1ParseError(
                        f"LL(1) Syntax error: no rule for ({top}, {current_type})"
                    )

        return self.trace
    
    def get_derivation(self):
        return self.derivation_log


class LL1_Grammar:
    def __init__(self):
        # Grammar
        self.productions = {
            "Program": [["StmtList", "EOF"]],

            "StmtList": [["Stmt", "StmtListPrime"]],
            "StmtListPrime": [["Stmt", "StmtListPrime"], [EPSILON]],

            "Stmt": [["Decl", "SEMICOLON"],
                     ["Assign", "SEMICOLON"],
                     ["IfStmt"],
                     ["WhileStmt"],
                     ["Block"],
                     ["PrintStmt", "SEMICOLON"]],

            "Decl": [["Type", "ID"]],
            "Type": [["INT"], ["FLOAT"]],

            "Assign": [["ID", "ASSIGN", "Expr"]],

            "IfStmt": [["IF", "LPAREN", "BoolExpr", "RPAREN", "Stmt", "ElsePart"]],
            "ElsePart": [["ELSE", "Stmt"], [EPSILON]],

            "WhileStmt": [["WHILE", "LPAREN", "BoolExpr", "RPAREN", "Stmt"]],

            "Block": [["LBRACE", "StmtList", "RBRACE"]],

            "PrintStmt": [["PRINT", "LPAREN", "Expr", "RPAREN"]],

            "Expr": [["Term", "ExprP"]],
            "ExprP": [["PLUS", "Term", "ExprP"],
                      ["MINUS", "Term", "ExprP"],
                      [EPSILON]],

            "Term": [["Factor", "TermP"]],
            "TermP": [["MUL", "Factor", "TermP"],
                      ["DIV", "Factor", "TermP"],
                      ["MOD", "Factor", "TermP"],
                      [EPSILON]],

            "Factor": [["ID"], ["INT_LIT"], ["FLOAT_LIT"], ["LPAREN", "ArithExpr", "RPAREN"]],

            "ArithExpr": [["Term", "ExprP"]],

            "BoolExpr": [["BoolOr"]],
            "BoolOr": [["BoolAnd", "BoolOrP"]],
            "BoolOrP": [["OR", "BoolAnd", "BoolOrP"], [EPSILON]],
            "BoolAnd": [["BoolNot", "BoolAndP"]],
            "BoolAndP": [["AND", "BoolNot", "BoolAndP"], [EPSILON]],

            "BoolNot": [["NOT", "BoolNot"],
                        ["ArithOrBoolExpr"]],
            
            "ArithOrBoolExpr": [["LPAREN", "BoolExpr", "RPAREN", "BoolNotP"],
                                ["ArithExpr", "BoolNotP"]],

            "RelOp": [["LT"], ["GT"], ["LE"], ["GE"], ["EQ"], ["NE"]],
        }

        self.start_symbol = "Program"

        self.non_terminals = set()
        self.terminals = set()

        self._compute_symbols()

    def _compute_symbols(self):
        # Non-terminals = keys
        self.non_terminals = set(self.productions.keys())

        # Terminals = symbols not in non-terminals
        for A in self.productions:
            for prod in self.productions[A]:
                for sym in prod:
                    if sym != EPSILON and sym not in self.productions:
                        self.terminals.add(sym)

    def __str__(self):
        result = []
        for A in self.productions:
            rhs_list = [" ".join(prod) for prod in self.productions[A]]
            result.append(f"{A} → {' | '.join(rhs_list)}")
        return "\n".join(result)