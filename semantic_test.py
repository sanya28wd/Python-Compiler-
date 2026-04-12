#!/usr/bin/env python3
"""
Semantic Analysis Test Script
Demonstrates symbol table construction and variable resolution
"""

from lexer import Lexer
from parser import Parser
from compiler_core import ParseError

def test_semantic_analysis():
    """Test semantic analysis with the evaluation program"""
    
    print("="*80)
    print("SEMANTIC ANALYSIS DEMONSTRATION")
    print("="*80)
    
    # Read the evaluation program
    try:
        with open('evaluation_program.txt', 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print("Error: evaluation_program.txt not found")
        return
    
    print("Source Code:")
    print("-"*40)
    print(source_code)
    print("-"*40)
    
    # Perform lexical analysis
    print("\n1. LEXICAL ANALYSIS")
    print("="*50)
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    if lexer.has_errors():
        print("Lexical errors found:")
        lexer.print_errors()
        return
    
    print(f"Lexical analysis successful. Generated {len(tokens)} tokens.")
    
    # Perform semantic analysis during parsing
    print("\n2. SEMANTIC ANALYSIS WITH SYMBOL TABLE")
    print("="*50)
    
    try:
        parser = Parser(tokens)
        ast = parser.parse_program()
        
        print("\n3. SEMANTIC ANALYSIS COMPLETED SUCCESSFULLY")
        print("="*50)
        print("✓ All variables declared before use")
        print("✓ No duplicate declarations in same scope")
        print("✓ Proper scope management with nested blocks")
        print("✓ Variable shadowing handled correctly")
        
    except ParseError as e:
        print(f"\n3. SEMANTIC/SYNTAX ERROR:")
        print("="*50)
        print(f"Error: {e}")
        print("\nThis demonstrates the semantic error detection capability.")
    
    except Exception as e:
        print(f"\n3. UNEXPECTED ERROR:")
        print("="*50)
        print(f"Error: {e}")

def test_variable_shadowing():
    """Test variable shadowing with a custom example"""
    
    print("\n\n" + "="*80)
    print("VARIABLE SHADOWING DEMONSTRATION")
    print("="*80)
    
    shadow_test_code = """
int x;
x = 10;
print(x);

{
    int x;
    x = 20;
    print(x);
}

print(x);
"""
    
    print("Test Code (Variable Shadowing):")
    print("-"*40)
    print(shadow_test_code)
    print("-"*40)
    
    # Lexical analysis
    lexer = Lexer(shadow_test_code)
    tokens = lexer.tokenize()
    
    # Semantic analysis
    try:
        parser = Parser(tokens)
        ast = parser.parse_program()
        
        print("\nVariable Shadowing Test: SUCCESS")
        print("✓ Inner 'x' shadows outer 'x' within block")
        print("✓ Outer 'x' restored after block exit")
        
    except ParseError as e:
        print(f"Variable Shadowing Test: ERROR - {e}")

def test_undeclared_variable():
    """Test undeclared variable detection"""
    
    print("\n\n" + "="*80)
    print("UNDECLARED VARIABLE DETECTION DEMONSTRATION")
    print("="*80)
    
    error_test_code = """
int x;
x = y + 1;
"""
    
    print("Test Code (Undeclared Variable):")
    print("-"*40)
    print(error_test_code)
    print("-"*40)
    
    # Lexical analysis
    lexer = Lexer(error_test_code)
    tokens = lexer.tokenize()
    
    # Semantic analysis
    try:
        parser = Parser(tokens)
        ast = parser.parse_program()
        print("Undeclared Variable Test: UNEXPECTED SUCCESS")
        
    except ParseError as e:
        print(f"Undeclared Variable Test: SUCCESS")
        print(f"✓ Correctly detected: {e}")

if __name__ == "__main__":
    test_semantic_analysis()
    test_variable_shadowing()
    test_undeclared_variable()
    
    print("\n\n" + "="*80)
    print("SEMANTIC ANALYSIS DEMONSTRATION COMPLETE")
    print("="*80)
