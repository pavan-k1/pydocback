import ast
import google.generativeai as genai
import ast
from generator import (
generate_docstring
)
from parsor import (
extract_nodes,get_existing_docstring,get_node_type
)

from inserter import(
clean_docstring,fix_file_formatting,insert_docstring_ast
)






def analyze_and_generate(filename, style):
   
    nodes,nod, source,tree = extract_nodes(filename)

    module_doc = generate_docstring(source,style,get_node_type(tree),get_existing_docstring(tree))
    module_doc = clean_docstring(module_doc)
    tree = insert_docstring_ast(tree, module_doc)

    for name,node, code_segment,existing_doc,node_type in nodes:
        is_empty = len(node.body) == 0 or all(isinstance(n, ast.Pass) for n in node.body)

        if is_empty:
             docstring = '"""TODO: Implement this function."""'
            

        else:
            
            docstring = generate_docstring(code_segment, style,node_type,existing_doc)
            docstring = clean_docstring(docstring) 
        node=insert_docstring_ast( node, docstring)

    source = ast.unparse(tree)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(source)
    fix_file_formatting(filename)