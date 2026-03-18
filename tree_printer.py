class Node:
   
    def __init__(self, type, children=None):
        self.type = type
        self.children = children if children is not None else []

    def __repr__(self):
        return f"Node({self.type})"


def print_tree(node, prefix="", is_last=True):
    """
    Prints the syntax tree in a human-readable format.
    """
    # Print the current node
    print(prefix + ("└── " if is_last else "├── ") + str(node.type))
    
    # Update the prefix for children
    child_prefix = prefix + ("    " if is_last else "│   ")
    
    if not hasattr(node, 'children'):
        return

    for i, child in enumerate(node.children):
        is_child_last = (i == len(node.children) - 1)
        if isinstance(child, Node):
            print_tree(child, child_prefix, is_child_last)
        else:
            # It's a terminal token (leaf)
            token_repr = f"{child.type} ('{child.value}')"
            print(child_prefix + ("└── " if is_child_last else "├── ") + token_repr)

