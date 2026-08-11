'''
IR: Instruction Representation
'''

class Instr:
    def __init__(self, raw):
        self.raw = raw.strip()
        self.label = None
        self.op = None
        self.arg1 = None
        self.arg2 = None
        self.result = None
        self.parse()
    
    def parse(self):
        line = self.raw

        if line.endswith(":"): #label
            self.label = line[:-1]
            return

        # print statement
        if line.startswith("print"):
            self.op = "print"
            self.arg1 = line.split()[1]
            return

        # if-goto
        if line.startswith("if"):
            # if a < b goto L3
            parts = line.split()
            self.op = "if"
            self.arg1 = parts[1]
            self.relop = parts[2]
            self.arg2 = parts[3]
            self.target = parts[5]
            return

        # goto
        if line.startswith("goto"):
            self.op = "goto"
            self.target = line.split()[1]
            return

        # assignment
        if "=" in line:
            left, right = map(str.strip, line.split("="))
            self.result = left

            parts = right.split()
            if len(parts) == 1:
                self.op = "="
                self.arg1 = parts[0]
            else:
                self.arg1 = parts[0]
                self.op = parts[1]
                self.arg2 = parts[2]
    
    def is_label(self):
        return self.label is not None

    def is_jump(self):
        return self.op in ["if", "goto"]

    def is_conditional(self):
        return self.op == "if"