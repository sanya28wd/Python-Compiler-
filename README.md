# Python-Compiler-

Full-stack Mini Compiler featuring all classical compilation phases: Lexical, Syntax, and Semantic Analysis. It manages Symbol Tables, generates Three-Address Code (TAC), and applies basic optimizations to produce Target Pseudo-assembly. Supports int/float, while loops, if-else, and complex boolean logic

This repository contains the full implementation of a Mini Compiler, designed to demonstrate the complete compilation pipeline from high-level source code to target pseudo-assembly. The project covers all classical phases of compilation, transforming a specific core language into a functional executable format.

SYSTEM ARCHITECTURE AND COMILER PHASE:

The compiler is built as a cumulative pipeline where each stage processes the output of the previous one. The architecture comprises:
1) Lexical Analysis: A robust scanner that uses regular expressions to categorize source text into a token stream, identifying keywords like int and while, as well as operators and identifiers.
   
2) Syntax Analysis:
A CFG-based parser (supporting LL(1) or Shift-Reduce methods) that validates program structure against a formal grammar. It generates parse trees and handles complex derivations for nested blocks and expressions.Semantic Analysis & Symbol Table: A central management system that tracks variable types, scopes, and memory offsets. It enforces strict type checking and detects errors such as undeclared variables or multiple declarations within the same scope.
   
3) Intermediate Code Generation (ICG):
The compiler translates validated code into Three-Address Code (TAC), utilizing temporary variables and jump labels to represent logical flow.

4) Optimization & Target Generation:
The final stages involve applying basic code optimizations to the TAC before generating Pseudo-assembly code that preserves the original program semantics.

LANGUAGE SPECIFICATION: 

The compiler is tailored to a specific core language supporting:
1. Data Types: int and float.
2. Control Flow: if-else statements and while loops.
3. Operators: A full suite of arithmetic ($+,-,*,/,\%$), relational ($<,>,<=,>=,==,!=$), and boolean ($&&, ||, !$) operators.
4. Structure: Variable declarations, assignment statements, and block structures using {}.
5. Verification: The system is rigorously tested against a prescribed evaluation program involving complex arithmetic, nested loops, and conditional logic to ensure the integrity of the compilation pipeline from source to target
