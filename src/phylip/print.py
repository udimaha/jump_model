from newick import NewickParser


def print_graphic_tree(tree: str):
    res = NewickParser(tree).parse()
    print("-"*10)
    print(f"PRINTING TREE! [{tree}]")
    print()
    res.root.print()
    print()
    print("DONE")
    print("-"*10)


def print_newick_tree(tree: str):
    res = NewickParser(tree).parse()
    print(f"Input: [{tree}]")
    out = res.root.to_newick()
    print(f"Output: [{out}]")
    print(f"Trees are the same: [{out == tree}]")
