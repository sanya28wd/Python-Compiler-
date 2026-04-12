"""
Main program for testing the Lexical Analyzer + Syntax Analyzer
"""

from lexer import Lexer
from compiler_core import TokenType, ParseError, Token as ParserToken, parse_with_nltk, SymbolTable
from parser import Parser
from ll1_parser import LL1Parser, LL1_Grammar
from slr_parser import build_slr_table, slr_parse, SLR_Grammar, print_slr_table
try:
    import nltk
except ImportError:
    nltk = None
import traceback

statement1_tokens = [
    'a', '=', '2', '*', '(', '3', '+', '4', ')', ';'
]
statement1_token_types = [
    'ID', '=', 'INT_LIT', '*', '(', 'INT_LIT', '+', 'INT_LIT', ')', ';'
]

statement2_tokens = [
    'while', '(', 'a', '<', 'b', '&&', 'b', '!=', '0', ')', '{', 'a', '=', 'a', '+', '1', ';', '}'
]
statement2_token_types = [
    'while', '(', 'ID', '<', 'ID', '&&', 'ID', '!=', 'INT_LIT', ')', '{', 'ID', '=', 'ID', '+', 'ID', ';', '}'
]

def print_trace(trace, title):
    print(f"\n=== {title} TRACE ===")
    print(f"{'Stack':<80} {'Input':<30} Action")
    print("-" * 150)
    for stack, current, action in trace:
        print(f"{str(stack):<80} {current:<30} {action}")


def display_menu():
    print("\n" + "="*80)
    print("COMPILER - PHASE 1 & 2: LEXICAL + SYNTAX ANALYSIS")
    print("="*80)
    print("1. Input source code from file")
    print("2. Input source code manually")
    print("3. Run example program")
    print("4. Exit")
    print("="*80)


def input_from_file():
    # Read source code from file
    try:
        filename = input("Enter the filename: ").strip()
        with open(filename, 'r') as f:
            source_code = f.read()
        return source_code
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def input_manually():
    # Input source code manually
    print("\nEnter your source code (type 'END' on a new line to finish):")
    print("-" * 80)
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break

    return "\n".join(lines)


def example_program():
    # Return an example program
    example = """
    int x;
    float y;
    x = 10;
    y = 3.14;

    if (x > 5) {
        print(x);
    }
    else {
        y = y + 2.5;
    }

    while (x > 0) {
        x = x - 1;
    }
    """
    return example


def sentential_form(symbols):
    """Convert a list of mixed strings/Trees to a readable sentential form."""
    parts = []
    for s in symbols:
        if isinstance(s, nltk.Tree):
            parts.append(s.label())
        else:
            parts.append(str(s))
    return ' '.join(parts)


def get_leftmost_derivation(tree):

    steps = []
    # Start with the root non-terminal
    symbols = [tree]
    steps.append(sentential_form(symbols))

    changed = True
    while changed:
        changed = False
        for i, sym in enumerate(symbols):
            if isinstance(sym, nltk.Tree):
                # Replace this non-terminal with its children
                symbols = symbols[:i] + list(sym) + symbols[i+1:]
                steps.append(sentential_form(symbols))
                changed = True
                break  # restart from leftmost each time
    return steps


def get_rightmost_derivation(tree):
   
    steps = []
    symbols = [tree]
    steps.append(sentential_form(symbols))
    
    changed = True
    while changed:
        changed = False
        # Scan from right to left to find the rightmost non-terminal
        for i in range(len(symbols) - 1, -1, -1):
            if isinstance(symbols[i], nltk.Tree):
                symbols = symbols[:i] + list(symbols[i]) + symbols[i+1:]
                steps.append(sentential_form(symbols))
                changed = True
                break  # restart from rightmost each time
    return steps


def split_into_statements(lexer_tokens):
   
    statements = []
    current = []
    brace_depth = 0
    i = 0

    while i < len(lexer_tokens):
        tok = lexer_tokens[i]
        if tok.type == TokenType.EOF:
            break

        current.append(tok)

        if tok.type == TokenType.LBRACE:
            brace_depth += 1
        elif tok.type == TokenType.RBRACE:
            brace_depth -= 1
            if brace_depth <= 0:
                brace_depth = 0
                # Peek ahead: if next non-whitespace token is ELSE, consume it too
                j = i + 1
                while j < len(lexer_tokens) and lexer_tokens[j].type == TokenType.EOF:
                    j += 1
                if j < len(lexer_tokens) and lexer_tokens[j].type == TokenType.ELSE:
                    i += 1
                    continue  # don't flush yet, keep building
                statements.append(current)
                current = []
        elif tok.type == TokenType.SEMICOLON and brace_depth == 0:
            statements.append(current)
            current = []

        i += 1

    if current:
        statements.append(current)
    return statements


def run_syntax_analysis(lexer_tokens):
    """
    1. Validates every statement in the program and reports errors.
    2. Shows the parse tree, leftmost derivation, and rightmost derivation
       for the FIRST statement only.
    """
    print("\n" + "="*80)
    print("SYNTAX ANALYSIS")
    print("="*80)

    statements = split_into_statements(lexer_tokens)
    if not statements:
        print("[ERROR] No statements found.")
        print("="*80)
        return

    # --- Part 1: Validate ALL statements ---
    print("\n--- Full Program Validation ---")
    all_valid = True
    first_tree = None
    
    # Create a single SymbolTable instance for the entire program
    symbol_table = SymbolTable()

    for idx, stmt_tokens in enumerate(statements):
        stmt_str = ' '.join(str(tok.value) for tok in stmt_tokens)
        #mapped = map_lexer_tokens_to_parser_tokens(stmt_tokens)
        nltk_types = [tok.type for tok in stmt_tokens]
    
        try:
            rd_parser = Parser(stmt_tokens, symbol_table)
            rd_parser.parse_stmt()

            # Ensure no leftover tokens remain for this statement
            if rd_parser.current().type != "EOF":
                tok = rd_parser.current()
                raise ParseError(
                    f"Syntax error at line {tok.line}, col {tok.column}: unexpected token {tok.type} ('{tok.value}') after statement"
                )

            trees = list(parse_with_nltk(nltk_types))
            print(f"  [OK]    Statement {idx+1}: {stmt_str}")
            if first_tree is None and trees:
                first_tree = trees[0]
                first_stmt_str = stmt_str

        except ParseError as e:
            # Report the parse error (contains line/column from tokens)
            print(f"  [ERROR] Statement {idx+1}: {stmt_str}  =>  {e}")
            all_valid = False
        except Exception as e:
            # Any other unexpected errors
            print(f"  [ERROR] Statement {idx+1}: {stmt_str}  =>  {e}")
            all_valid = False

    if all_valid:
        print("\n[SUCCESS] All statements are syntactically valid.")
    else:
        print("\n[WARNING] Some statements have syntax errors (see above).")
    
    # Print final symbol table state after all statements
    print("\n" + "="*80)
    print("FINAL SYMBOL TABLE STATE (After Full Program Validation)")
    print("="*80)
    symbol_table.print_current_state()
    print("="*80)

    #  Tree & Derivations for FIRST statement only 
    if first_tree is None:
        print("\n[ERROR] Could not parse the first statement for tree/derivation display.")
        print("="*80)
        return

    print("\n" + "="*80)
    print(f"PARSE TREE  (First Statement: {first_stmt_str})")
    print("="*80)
    first_tree.pretty_print()

    print("\n" + "="*80)
    print(f"LEFTMOST DERIVATION  (First Statement: {first_stmt_str})")
    print("="*80)
    for i, step in enumerate(get_leftmost_derivation(first_tree)):
        if i == 0:
            print(f"  {step}")
        else:
            print(f"  => {step}")

    print("\n" + "="*80)
    print(f"RIGHTMOST DERIVATION  (First Statement: {first_stmt_str})")
    print("="*80)
    for i, step in enumerate(get_rightmost_derivation(first_tree)):
        if i == 0:
            print(f"  {step}")
        else:
            print(f"  => {step}")

    print("="*80)


def analyze_code(source_code):
    # This function will now perform both lexical and syntax analysis
    if not source_code or not source_code.strip():
        print("Error: No source code provided")
        return
    
    choice = input("Enter L for LL(1) Parser and S for SLR Parser: ").strip().upper()


    # 1. Lexical Analysis
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    print("\n" + "="*80)
    print("LEXICAL ANALYSIS")
    print("="*80)
    lexer.print_tokens()
    
    if lexer.has_errors():
        lexer.print_errors()
        print("\nHalting analysis due to lexical errors.")
        return # Stop if there are lexical errors
    else:
        print("\nLexical analysis completed successfully.")

    # 2. Syntax Analysis
    run_syntax_analysis(tokens)

    if choice == 'L':
        # 3. LL(1) Parser
        print("\n=== LL(1) PARSER ===")
        try:
            grammar_obj = LL1_Grammar()
            ll1_parser = LL1Parser(tokens)
            table = ll1_parser.build_ll1_table(grammar_obj.productions, grammar_obj.start_symbol)
            ll1_parser.print_ll1_table(grammar_obj, table)
            ll1_trace = ll1_parser.parse()
            print_trace(ll1_trace, "LL(1)")
            print("\nLL(1) Parsing successful!")

        except Exception as e:
            print("LL(1) Error:", e)
            traceback.print_exc()
        
    elif choice == 'S':
        # 4. SLR Parser
        print("\n=== SLR PARSER ===")
        try:
            grammar_obj = SLR_Grammar()
            ACTION, GOTO, states, grammar = build_slr_table(grammar_obj.productions, grammar_obj.start_symbol)
            print_slr_table(grammar_obj, ACTION, GOTO, states)            
            tokens = [t.type for t in tokens] + ["$"]
            result = slr_parse(tokens, ACTION, GOTO)
            if result:
                print("\nSLR Parsing completed successfully!")
            else:
                print("\nSLR Parsing failed.")

        except Exception as e:
            print("SLR Error:", e)
            traceback.print_exc()


def demonstrate_nltk_parsing():
    """
    Uses NLTK to parse the two non-trivial statements and show their trees.
    """
    print("\n" + "="*80)
    print("NLTK SYNTACTIC VALIDATION DEMONSTRATION")
    print("="*80)

    # --- Process Statement 1 ---
    print("\n--- Analyzing: a = 2 * (3 + 4); ---")
    trees1 = list(parse_with_nltk(statement1_token_types))
    if trees1:
        print("\n[SUCCESS] Statement 1 is syntactically valid.")
        
        
        print("\nParse Tree for Statement 1:")
        trees1[0].pretty_print()
    else:
        print("\n[FAILURE] Statement 1 is syntactically invalid.")

    print("\n\n--- Analyzing: while (a < b && b != 0) { a = a + 1; } ---")
    trees2 = list(parse_with_nltk(statement2_token_types))
    if trees2:
        print("\n[SUCCESS] Statement 2 is syntactically valid.")
        print("\nParse Tree for Statement 2:")
        trees2[0].pretty_print()
    else:
        print("\n[FAILURE] Statement 2 is syntactically invalid.")
    
    print("\n" + "="*80)
    print("Note on Derivations:")
    print("NLTK's built-in parsers do not provide a simple public API to get a clean, step-by-step derivation log.")
    print("The parse tree itself is the primary output that visually represents the derivation process.")
    print("For the report, the manual derivations I provided earlier should be used.")
    print("="*80)


def main():
    while True:
        display_menu()
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            source_code = input_from_file()
            if source_code:
                analyze_code(source_code)

        elif choice == "2":
            source_code = input_manually()
            if source_code:
                analyze_code(source_code)

        elif choice == "3":
            source_code = example_program()
            print("\nRunning example program:")
            print("-" * 80)
            print(source_code)
            print("-" * 80)
            analyze_code(source_code)
        
        elif choice == "4":
            print("Exiting compiler")
            break
        
        else:
            print("Invalid choice! Please try again.")


if __name__ == "__main__":
    main()
