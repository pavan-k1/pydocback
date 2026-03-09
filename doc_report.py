import ast



def docstring_coverage(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        source = f.read()
        tree = ast.parse(source)

    total_nodes = 0
    documented_nodes = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            total_nodes += 1
            if ast.get_docstring(node):
                documented_nodes += 1

    if total_nodes == 0:
        print("No functions, classes, or modules found.")
        return 0

    coverage = (documented_nodes / total_nodes) * 100
    return coverage