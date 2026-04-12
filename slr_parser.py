from dataclasses import dataclass
from typing import List, Dict, Tuple, Set, FrozenSet
from first_follow import FirstFollow

EPSILON = "ε"

# LR(0) item
@dataclass(frozen=True)
class Item:
    lhs: str
    rhs: Tuple[str, ...]
    dot: int

    def __str__(self):
        before = " ".join(self.rhs[:self.dot])
        after = " ".join(self.rhs[self.dot:])
        return f"{self.lhs} → {before} • {after}".strip()


# closure
def closure(items, grammar):
    closure_set = set(items)
    changed = True

    while changed:
        changed = False
        new_items = set()

        for item in closure_set:
            if item.dot < len(item.rhs):
                sym = item.rhs[item.dot]

                if sym in grammar:
                    for prod in grammar[sym]:
                        if prod == ['ε'] or prod == [EPSILON]:
                            new_items.add(Item(sym, (EPSILON,), 1))
                        else:
                            new_items.add(Item(sym, tuple(prod), 0))

        if new_items - closure_set:
            closure_set |= new_items
            changed = True

    return frozenset(closure_set)


# goto
def goto(items, symbol, grammar):
    moved = set()

    for item in items:
        if item.dot < len(item.rhs) and item.rhs[item.dot] == symbol:
            moved.add(Item(item.lhs, item.rhs, item.dot + 1))

    return closure(moved, grammar) if moved else frozenset()


# canonical collection
def build_states(grammar, start):
    grammar = dict(grammar)
    aug = start + "'"
    grammar[aug] = [(start,)]

    start_item = Item(aug, (start,), 0)
    C = [closure({start_item}, grammar)]

    symbols = set()
    for k, v in grammar.items():
        symbols.add(k)
        for p in v:
            symbols.update(p)

    changed = True
    while changed:
        changed = False

        for state in list(C):
            for sym in symbols:
                nxt = goto(state, sym, grammar)
                if nxt and nxt not in C:
                    C.append(nxt)
                    changed = True

    return C, grammar


# build slr table
def build_slr_table(grammar, start):
    states, grammar = build_states(grammar, start)
    ff_obj = FirstFollow(grammar, start)
    ff_obj.compute_first() 
    ff_obj.compute_follow()
    
    follow = ff_obj.FOLLOW

    ACTION = {}
    GOTO = {}

    index = {s: i for i, s in enumerate(states)}

    for i, state in enumerate(states):

        for item in state:

            # shift
            if item.dot < len(item.rhs):
                sym = item.rhs[item.dot]
                nxt = goto(state, sym, grammar)

                if nxt:
                    j = index[nxt]

                    if sym not in grammar:
                        ACTION[(i, sym)] = ("shift", j)
                    else:
                        GOTO[(i, sym)] = j

            # reduce
            else:
                # accept
                if item.lhs == start + "'":
                    ACTION[(i, "$")] = ("accept",)

                else:
                    for a in follow[item.lhs]:
                        if (i, a) in ACTION and ACTION[(i, a)][0] == "shift":
                            continue    #in case of shift-reduce conflict, prefer shift
                        
                        ACTION[(i, a)] = ("reduce", (item.lhs, item.rhs))
                        
    return ACTION, GOTO, states, grammar

def print_slr_table(grammar_obj, ACTION, GOTO, states):
    print("SLR PARSE TABLE:\n")

    terminals = list(grammar_obj.terminals) + ["$"]
    non_terminals = list(grammar_obj.productions.keys())

    for i in range(len(states)):
        print(f"# State {i}")

        # ACTION part
        for t in terminals:
            if (i, t) in ACTION:
                act = ACTION[(i, t)]

                if act[0] == "shift":
                    print(f'    ACTION[({i}, "{t}")] = ("shift", {act[1]})')

                elif act[0] == "reduce":
                    lhs, rhs = act[1]
                    rhs_str = ", ".join(f'"{sym}"' for sym in rhs)
                    print(f'    ACTION[({i}, "{t}")] = ("reduce", ("{lhs}", [{rhs_str}]))')

                elif act[0] == "accept":
                    print(f'    ACTION[({i}, "{t}")] = ("accept",)')

        # GOTO part
        for nt in non_terminals:
            if (i, nt) in GOTO:
                print(f'    GOTO[({i}, "{nt}")] = {GOTO[(i, nt)]}')

        print()

# parser
def slr_parse(tokens, ACTION, GOTO):
    stack = [0]
    i = 0

    print("\n=== SLR TRACE ===")

    while True:
        state = stack[-1]
        lookahead = tokens[i] if i < len(tokens) else "$"

        action = ACTION.get((state, lookahead))

        print(f"Stack: {stack} | Input: {tokens[i:]} | Action: {action}")

        if not action:
            print("❌ ERROR: No valid action")
            return False

        if action[0] == "shift":
            stack.append(lookahead)
            stack.append(action[1])
            i += 1

        elif action[0] == "reduce":
            lhs, rhs = action[1]

            if rhs != ("ε",):
                for _ in rhs:
                    stack.pop() #pop state
                    stack.pop() #pop symbol (for every symbol in beta, pop twice)

            state = stack[-1]
            goto_state = GOTO.get((state, lhs))

            if goto_state is None:
                print(f"Missing GOTO for state {state} and {lhs}")
                return False
            
            stack.append(lhs)
            stack.append(goto_state)

        elif action[0] == "accept":
            print("ACCEPTED")
            return True


class SLR_Grammar:
    def __init__(self):
        self.productions = {
            "Program": [["StmtList", "EOF"]],
            "StmtList": [["Stmt", "StmtList"],
                         [("ε")]],
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
            "ElsePart": [["ELSE", "Stmt"], [("ε")]],
            "WhileStmt": [["WHILE", "LPAREN", "BoolExpr", "RPAREN", "Stmt"]],
            "Block": [["LBRACE", "StmtList", "RBRACE"]],
            "PrintStmt": [["PRINT", "LPAREN", "Expr", "RPAREN"]],
            "Expr": [["Term", "ExprP"]],
            "ExprP": [["PLUS", "Term", "ExprP"],
                      ["MINUS", "Term", "ExprP"],
                      [("ε")]],
            "Term": [["Factor", "TermP"]],
            "TermP": [["MUL", "Factor", "TermP"],
                      ["DIV", "Factor", "TermP"],
                      ["MOD", "Factor", "TermP"],
                      [("ε")]],
            "Factor": [["ID"], ["INT_LIT"], ["FLOAT_LIT"], ["LPAREN", "Expr", "RPAREN"]],
            "BoolExpr": [["BoolOr"]],
            "BoolOr": [["BoolAnd", "BoolOrP"]],
            "BoolOrP": [["OR", "BoolAnd", "BoolOrP"], [("ε")]],
            "BoolAnd": [["BoolNot", "BoolAndP"]],
            "BoolAndP": [["AND", "BoolNot", "BoolAndP"], [("ε")]],
            "BoolNot": [["NOT", "BoolNot"],
                        ["LPAREN", "BoolExpr", "RPAREN"],
                        ["RelExpr"]],
            "RelExpr": [["Expr", "RelTail"]],
            "RelTail": [["RelOp", "Expr"], [("ε")]],
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