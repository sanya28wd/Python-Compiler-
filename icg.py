"""
Intermediate Code Generator (ICG)
Generates Three-Address Code (TAC) from the Abstract Syntax Tree (AST)
Optimizes TAC using logic from optimizer.py
"""

from compiler_core import Node
from optimizer import optimize
from ir import Instr
from cfg import build_basic_blocks, build_cfg

class IntermediateCodeGenerator:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.code = []

    def new_temp(self):
        """Generate a new temporary variable (e.g., t0, t1)."""
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def new_label(self):
        """Generate a new jump label (e.g., L0, L1)."""
        l = f"L{self.label_count}"
        self.label_count += 1
        return l

    def emit(self, instruction):
        """Append a new TAC instruction to the code list."""
        self.code.append(instruction)

    def generate(self, ast_root):
        """Start TAC generation from the root of the AST."""
        self.code = []
        self.temp_count = 0
        self.label_count = 0
        
        print("\n" + "="*80)
        print("INTERMEDIATE CODE GENERATION (THREE-ADDRESS CODE)")
        print("="*80)
        
        self.generate_stmt(ast_root)
        
        # Print the generated code
        print("\n--- Generated 3AC ---")
        for i, instr in enumerate(self.code):
            if instr.endswith(":"):
                print(f"{(i+1)}) {instr}")
            else:
                print(f"{(i+1)})    {instr}")
                
        # Apply optimization — use self.code (list of strings) as tac_lines
        tac_lines = self.code 

        instructions = [Instr(line) for line in tac_lines]

        # Build BB + CFG
        blocks, label_map, leader_map, leaders = build_basic_blocks(instructions)
        cfg = build_cfg(blocks, label_map)

        #print("\n=== BASIC BLOCKS ===")
        #for b in cfg:
        #    print(b)
        
        print("\n=== LEADERS ===")
        print("Leaders:", ", ".join(str(idx + 1) for idx in leaders))

        print("\n=== BASIC BLOCKS ===")
        line_no = 1  # global instruction counter

        for i, b in enumerate(cfg):
            print(f"\nBlock {i}:")
            
            for instr in b.instructions: 
                if instr.label is not None:
                    print(f"{line_no}) {instr.raw}")
                else:
                    print(f"{line_no})     {instr.raw}")
                line_no += 1
            
        print("\n=== CFG ===")
        for b in cfg:
            print(f"Block {b.id} -> {[s.id for s in b.successors]}")

        # Optimize operates on raw string lines, not CFG
        optimized_lines = optimize(tac_lines)

        print("\n--- Optimized 3AC ---")
        for i, instr in enumerate(optimized_lines):
            if instr.endswith(":"):
                print(f"{(i+1)}) {instr}")
            else:
                print(f"{(i+1)})    {instr}")
        print("="*80)



        #side by side table for better comparison
        print("\n" + "="*80)
        print(f"{'--- Generated 3AC ---':<{35}} {'--- Optimized 3AC ---'}")
        print("-"*80)
        
        max_lines = max(len(self.code), len(optimized_lines))
        
        for i in range(max_lines):
            # Format original line
            if i < len(self.code):
                instr = self.code[i]
                if instr.endswith(":"):
                    left = f"{i+1}) {instr}"
                else:
                    left = f"{i+1})    {instr}"
            else:
                left = ""
            
            # Format optimized line
            if i < len(optimized_lines):
                instr = optimized_lines[i]
                if instr.endswith(":"):
                    right = f"{i+1}) {instr}"
                else:
                    right = f"{i+1})    {instr}"
            else:
                right = ""
            
            print(f"{left:<{35}} {right}")
        
        print("="*80)
        return optimized_lines

    def generate_stmt(self, node):
        """Process statement nodes (Assignments, Ifs, Whiles, Blocks)."""
        # If it's a Token (leaf), skip it for statement processing
        if not hasattr(node, "children"):
            return

        if node.type in ("Program", "Stmt", "StmtList", "Block"):
            for child in node.children:
                self.generate_stmt(child)
                
        elif node.type == "Decl":
            # Variable declarations don't require TAC in this standard format
            pass
            
        elif node.type == "Assign":
            # Assign -> ID ASSIGN Expr
            id_val = node.children[0].value
            expr_val = self.generate_expr(node.children[2])
            self.emit(f"{id_val} = {expr_val}")
            
        elif node.type == "PrintStmt":
            # PrintStmt -> PRINT LPAREN Expr RPAREN
            expr_val = self.generate_expr(node.children[2])
            self.emit(f"print {expr_val}")
            
        elif node.type == "IfStmt":
            # IfStmt -> IF LPAREN BoolExpr RPAREN Stmt (ELSE Stmt)?
            t_label = self.new_label()
            f_label = self.new_label()
            
            bool_node = node.children[2]
            stmt_true = node.children[4]
            
            if len(node.children) > 5:  # Has ELSE block
                end_label = self.new_label()
                self.generate_bool(bool_node, t_label, f_label)
                
                self.emit(f"{t_label}:")
                self.generate_stmt(stmt_true)
                self.emit(f"goto {end_label}")
                
                self.emit(f"{f_label}:")
                self.generate_stmt(node.children[6])  # The ELSE Stmt
                
                self.emit(f"{end_label}:")
            else:  # No ELSE block
                self.generate_bool(bool_node, t_label, f_label)
                
                self.emit(f"{t_label}:")
                self.generate_stmt(stmt_true)
                
                self.emit(f"{f_label}:")
                
        elif node.type == "WhileStmt":
            # WhileStmt -> WHILE LPAREN BoolExpr RPAREN Stmt
            start_label = self.new_label()
            t_label = self.new_label()
            f_label = self.new_label()
            
            self.emit(f"{start_label}:")
            self.generate_bool(node.children[2], t_label, f_label)
            
            self.emit(f"{t_label}:")
            self.generate_stmt(node.children[4])
            self.emit(f"goto {start_label}")
            
            self.emit(f"{f_label}:")

    def generate_expr(self, node):
        """Process arithmetic expressions and generate temporaries."""
        if not hasattr(node, "children"):
            return str(node.value)  # Base case: Token (ID or Literal)
            
        if node.type == "Factor":
            if len(node.children) == 1:
                return str(node.children[0].value)
            elif len(node.children) == 3:  # LPAREN Expr RPAREN
                return self.generate_expr(node.children[1])
                
        elif node.type in ("Expr", "Term", "RelExpr"):
            if len(node.children) == 1:
                return self.generate_expr(node.children[0])
            elif len(node.children) == 3:
                left = self.generate_expr(node.children[0])
                right = self.generate_expr(node.children[2])
                op = node.children[1].value
                t = self.new_temp()
                self.emit(f"{t} = {left} {op} {right}")
                return t
                
        return ""

    def generate_bool(self, node, t_label, f_label):
        """Process boolean logic with short-circuit evaluation."""
        if not hasattr(node, "children"):
            return

        if node.type == "BoolOr":
            if len(node.children) == 3:
                l1 = self.new_label()
                self.generate_bool(node.children[0], t_label, l1)
                self.emit(f"{l1}:")
                self.generate_bool(node.children[2], t_label, f_label)
            else:
                self.generate_bool(node.children[0], t_label, f_label)
                
        elif node.type == "BoolAnd":
            if len(node.children) == 3:
                l1 = self.new_label()
                self.generate_bool(node.children[0], l1, f_label)
                self.emit(f"{l1}:")
                self.generate_bool(node.children[2], t_label, f_label)
            else:
                self.generate_bool(node.children[0], t_label, f_label)
                
        elif node.type == "BoolNot":
            if getattr(node.children[0], "type", None) == "NOT":
                self.generate_bool(node.children[1], f_label, t_label) # Flip labels
            elif getattr(node.children[0], "type", None) == "LPAREN":
                self.generate_bool(node.children[1], t_label, f_label)
            else:
                self.generate_bool(node.children[0], t_label, f_label)
                
        elif node.type == "RelExpr":
            if len(node.children) == 3:
                left = self.generate_expr(node.children[0])
                right = self.generate_expr(node.children[2])
                op = node.children[1].value
                self.emit(f"if {left} {op} {right} goto {t_label}")
                self.emit(f"goto {f_label}")
            else:
                val = self.generate_expr(node.children[0])
                self.emit(f"if {val} != 0 goto {t_label}")
                self.emit(f"goto {f_label}")