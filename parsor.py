import ast
import os


def get_existing_docstring(node):
    return ast.get_docstring(node)


def get_node_type(node):
    if isinstance(node, ast.Module):
        return "module"
    elif isinstance(node, ast.ClassDef):
        return "class"
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "function"





def extract_nodes(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        source = f.read()
        tree = ast.parse(source)
    nod=[]
    nodes = []


    module_name = os.path.basename(filename)
    nod.append({
        "id": module_name,
        "name": module_name,
        "type": "module",
        "parent": None,
        "hasDocstring": bool(ast.get_docstring(tree))
    })
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            nodes.append((node.name, node, ast.get_source_segment(source, node), ast.get_docstring(node),get_node_type(node)))
            nod.append({"id": node.name,"name": node.name,"type": "class","parent": None,"hasDocstring": bool(ast.get_docstring(node)) })
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nodes.append((f"{node.name}.{child.name}", child,
                    ast.get_source_segment(source, child),
                    ast.get_docstring(child),get_node_type(child)))
                    nod.append({"id": f"{node.name}.{child.name}","name": child.name,"type": "method","parent": node.name,"hasDocstring": bool(ast.get_docstring(child))
                    })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes.append((node.name, node, ast.get_source_segment(source, node), ast.get_docstring(node),get_node_type(node)))
            nod.append({"id": node.name,"name": node.name,"type": "function","parent": None,"hasDocstring": bool(ast.get_docstring(node))})

    return nodes,nod,source,tree

