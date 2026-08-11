'''
This file will detect leaders, build basic blocks and build CFG (Control Flow Graph)
'''

from ir import Instr

class BasicBlock:
    def __init__(self, id):
        self.id = id
        self.instructions = []
        self.successors = []
        self.predecessors = []

    def add_instruction(self, instr):
        self.instructions.append(instr)

    def __repr__(self):
        lines = [f"Block {self.id}:"]
        for instr in self.instructions:
            lines.append(f"  {instr.raw}")
        return "\n".join(lines)

#leader detection
def find_leaders(instructions):
    leaders = set()

    # Rule 1: first instruction
    leaders.add(0)

    label_to_index = {}

    # First pass: map labels
    for i, instr in enumerate(instructions):
        if instr.raw.endswith(":"):
            label = instr.raw[:-1]
            label_to_index[label] = i
            leaders.add(i)

    # Second pass: jumps
    for i, instr in enumerate(instructions):
        text = instr.raw

        if text.startswith("if"):
            parts = text.split()
            target = parts[-1]
            if target in label_to_index:
                leaders.add(label_to_index[target])
            if i + 1 < len(instructions):
                leaders.add(i + 1)

        elif text.startswith("goto"):
            target = text.split()[1]
            if target in label_to_index:
                leaders.add(label_to_index[target])
            if i + 1 < len(instructions):
                leaders.add(i + 1)

    return sorted(leaders), label_to_index

#build basic blocks
def build_basic_blocks(instructions):
    leaders, label_map = find_leaders(instructions)

    blocks = []
    leader_to_block = {}

    for i, leader in enumerate(leaders):
        block = BasicBlock(i)
        leader_to_block[leader] = block
#until next leader -1
        end = leaders[i + 1] if i + 1 < len(leaders) else len(instructions)

        for j in range(leader, end):
            block.add_instruction(instructions[j])

        blocks.append(block)

    return blocks, label_map, leader_to_block, leaders

#build cfg
def build_cfg(blocks, label_map):
    # Map label → block
    label_to_block = {}

    for block in blocks:
        first_instr = block.instructions[0]
        if first_instr.raw.endswith(":"):
            label = first_instr.raw[:-1]
            label_to_block[label] = block

    for i, block in enumerate(blocks):
        last_instr = block.instructions[-1].raw

        # IF
        if last_instr.startswith("if"):
            parts = last_instr.split()
            target = parts[-1]

            if target in label_to_block:
                block.successors.append(label_to_block[target])

            # fall-through
            if i + 1 < len(blocks):
                block.successors.append(blocks[i + 1])

        # GOTO
        elif last_instr.startswith("goto"):
            target = last_instr.split()[1]

            if target in label_to_block:
                block.successors.append(label_to_block[target])

        # NORMAL FLOW
        else:
            if i + 1 < len(blocks):
                block.successors.append(blocks[i + 1])

    # Fill predecessors
    for block in blocks:
        for succ in block.successors:
            succ.predecessors.append(block)

    return blocks

