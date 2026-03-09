import ast
import subprocess
import sys
import os

def clean_docstring(docstring: str) -> str:
    if not docstring:
        docstring = "Provide functionality as described."

    docstring = str(docstring).strip()
    docstring = docstring.replace("\\n", "\n")         
    docstring = docstring.replace("```python", "")    
    docstring = docstring.replace("```", "")
    if not (docstring.startswith('"""') and docstring.endswith('"""')):
        docstring = f'"""{docstring}"""'
    return docstring




def fix_file_formatting(filename: str):
    try:
        subprocess.run(
            [sys.executable, "-m", "docformatter", "-i", filename], check=True
        )
    except subprocess.CalledProcessError as e:
             pass

def insert_docstring_ast(node, docstring):
    docstring = docstring.strip().replace('"""', "")
    docstring = ast.Expr(value=ast.Constant(value=docstring))

    if ast.get_docstring(node):
        node.body[0] = docstring
    else:
        node.body.insert(0, docstring)

    return node
