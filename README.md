# Python-Compiler-

Full-stack Mini Compiler demonstrating lexical, syntax, and semantic analysis, symbol table management, three-address code (TAC) generation, basic optimizations, and pseudo-assembly output. Supports int/float, if-else, while, and complex boolean logic.

Summary of recent update
-------------------------
Applied the CC_LAB_WEEK7 bundle (added/updated lexer, parser, semantic, ICG, optimizer, and helper modules). The change includes example programs and utilities (AST and LL(1) table dumps).

Quick usage
-----------
- Interactive menu: python3 main.py
- Run the built-in example non-interactively:
  python3 -c "from main import example_program, analyze_code; analyze_code(example_program())"

Key modules added/updated
-------------------------
- lexer.py, parser.py, compiler_core.py, icg.py, optimizer.py, ir.py, ll1_parser.py, first_follow.py, slr_parser.py
- Helper files: ast_structure.txt, ll1_table.txt, sample_program.txt, semantic_cases.txt

Notes
-----
Files from CC_LAB_WEEK7 were integrated and committed on branch sanya28wd-apply-lab7-updates. AST and LL(1) table outputs are written to ast_structure.txt and ll1_table.txt when running the example.

If anything specific should be adjusted (tests, packaging, or CLI behavior), reply with details and changes will be made.
