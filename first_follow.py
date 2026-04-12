EPSILON = "ε"

class FirstFollow:
    def __init__(self, productions, start_symbol):
        self.productions = productions
        self.start_symbol = start_symbol

        self.non_terminals = set(productions.keys())
        self.terminals = self._get_terminals()

        self.FIRST = {nt: set() for nt in self.non_terminals}
        self.FOLLOW = {nt: set() for nt in self.non_terminals}

        self.compute_first()
        self.compute_follow()

    def _get_terminals(self):
        terminals = set()
        for rhs_list in self.productions.values():
            for rhs in rhs_list:
                for sym in rhs:
                    if sym not in self.productions and sym != EPSILON:
                        terminals.add(sym)
        return terminals

    # first
    def compute_first(self):
        changed = True

        while changed:
            changed = False

            for A in self.productions:
                for production in self.productions[A]:

                    # ε production
                    if production == (EPSILON,) or production == [EPSILON]:
                        if EPSILON not in self.FIRST[A]:
                            self.FIRST[A].add(EPSILON)
                            changed = True
                        continue

                    for symbol in production:
                        if symbol in self.terminals:
                            if symbol not in self.FIRST[A]:
                                self.FIRST[A].add(symbol)
                                changed = True
                            break

                        elif symbol in self.non_terminals:
                            before = len(self.FIRST[A])
                            self.FIRST[A].update(self.FIRST[symbol] - {EPSILON})
                            if len(self.FIRST[A]) > before: 
                                changed = True

                            if EPSILON in self.FIRST[symbol]:
                                continue
                            else:
                                break

                        else:
                            break
                    else:
                        # all symbols had ε
                        if EPSILON not in self.FIRST[A]:
                            self.FIRST[A].add(EPSILON)
                            changed = True

    # follow
    def compute_follow(self):
        self.FOLLOW[self.start_symbol].add("$")

        changed = True

        while changed:
            changed = False

            for A in self.productions:
                for production in self.productions[A]:

                    for i, B in enumerate(production):
                        if B not in self.non_terminals:
                            continue

                        beta = production[i + 1:]

                        if beta:
                            first_beta = self.first_of_string(beta)

                            before = len(self.FOLLOW[B])
                            self.FOLLOW[B].update(first_beta - {EPSILON})

                            if EPSILON in first_beta:
                                self.FOLLOW[B].update(self.FOLLOW[A])

                            if len(self.FOLLOW[B]) > before:
                                changed = True
                        else:
                            before = len(self.FOLLOW[B])
                            self.FOLLOW[B].update(self.FOLLOW[A])

                            if len(self.FOLLOW[B]) > before:
                                changed = True


    def first_of_string(self, symbols):  #symbols means grammar symbols
        result = set()

        for symbol in symbols:
            if symbol == EPSILON:
                continue
                
            if symbol in self.terminals:
                result.add(symbol)
                return result

            elif symbol in self.non_terminals:
                result.update(self.FIRST[symbol] - {EPSILON})

                if EPSILON in self.FIRST[symbol]:
                    continue
                else:
                    return result

        result.add(EPSILON)
        return result
    
    def get_follow(self, non_terminal):
        """Get FOLLOW set for a non-terminal"""
        return self.FOLLOW.get(non_terminal, set())

    # print
    def print_first(self):
        print("\nFIRST sets:")
        for nt in self.FIRST:
            print(f"{nt}: {self.FIRST[nt]}")

    def print_follow(self):
        print("\nFOLLOW sets:")
        for nt in self.FOLLOW:
            print(f"{nt}: {self.FOLLOW[nt]}")
