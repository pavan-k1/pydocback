import google.generativeai as genai
import ast
import os
from dotenv import load_dotenv
load_dotenv()


def generate_docstring(code_segment, style,node_type,existing_docstring=None):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    Styles = {
        "google": "Follow Google Python docstring style.",
        "numpy": "Follow NumPy docstring style.",
        "rest": "Follow reStructuredText docstring style."
    }

    if style not in Styles:   
        style = "google"
    
    if node_type=="function":
     if existing_docstring:
      prompt = f'''
           
           You are an expert Python developer.
           Ensure that the following existing docstring fully follows {Styles[style]} style and PEP 257 conventions.
           If it does not match the requested style or is incomplete, rewrite and complete it properly.
           Return only the corrected docstring (no code, no extra quotes)
           Include a summary, parameters with types, return type, and description.
           Do NOT include the function code, code fences, or extra quotes.
          this type of error must not be there D401: First line should be in imperative mood (perhaps 'Determine', not 'Determines')
       {Styles[style]}

       Function:
       {code_segment}
     Existing docstring:
  \"\"\"{existing_docstring}\"\"\" 
''' 
     else:
       prompt = f'''
           You are an expert Python developer.
           Generate Python docstring (triple-quoted) PEP257 validated for the following function.
           Include a summary, parameters with types, return type, and description.
           Do NOT include the function code, code fences, or extra quotes.
           this type of error must not be there D401: First line should be in imperative mood (perhaps 'Determine', not 'Determines')

       {Styles[style]}

       Function:
       {code_segment}
      '''
    elif node_type=="class":
     if existing_docstring:
      prompt = f'''
           
           You are an expert Python developer.
           Ensure that the following existing docstring fully follows {Styles[style]} style and PEP 257 conventions.
           If it does not match the requested style or is incomplete, rewrite and complete it properly.
           Return only the corrected docstring (no code, no extra quotes)
           Do NOT include the function code, code fences, or extra quotes.
           this type of error must not be there D401: First line should be in imperative mood (perhaps 'Determine', not 'Determines')
       {Styles[style]}

       Class
       {code_segment}
     Existing docstring:
  \"\"\"{existing_docstring}\"\"\" 
''' 
     else:
       prompt = f'''
           You are an expert Python developer.
           Generate Python docstring (triple-quoted) PEP257 validated for the following Class in just 2-3 lines.
           Do NOT include the function code, code fences, or extra quotes.
          this type of error must not be there D401: First line should be in imperative mood (perhaps 'Determine', not 'Determines')

       {Styles[style]}

       Class:
       {code_segment}
      '''
    elif node_type=="module":
       prompt = f'''
           You are an expert Python developer.
           Generate Python docstring (triple-quoted) PEP257 validated for the following Module in just two lines.
           Do NOT include the function code, code fences, or extra quotes.
           this type of error must not be there D401: First line should be in imperative mood (perhaps 'Determine', not 'Determines')

       {Styles[style]}

       Module:
       {code_segment}
      '''     

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini has some problem:", e)
        print("There is some problem Hence,Docstring generation failed. trying hugging face fallback")

    try:
        from groq import Groq

        client = Groq(api_key="Enter your API key here")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content.strip()

    except Exception as groq_error:
        print("Groq fallback failed:", groq_error)
        return template_docstring_generator(code_segment, style, node_type)



import ast
from typing import Any


def template_docstring_generator(code_segment: str, style: str, node_type: str) -> str:
    """
    Fully self-contained AST-based fallback docstring generator.
    Style-aware, PEP257 compliant, and guaranteed non-null output.
    """
    
    # ---------------- SAFE DEFAULT ---------------- #
    DEFAULT_DOCSTRING = '''"""
Perform the described operation.
"""'''

    try:
        tree = ast.parse(code_segment)
    except Exception:
        return DEFAULT_DOCSTRING

    style = (style or "google").lower()

    # ---------------- UTILITIES ---------------- #

    def safe_unparse(annotation):
        if annotation is None:
            return "Any"
        try:
            return ast.unparse(annotation)
        except Exception:
            return "Any"

    def extract_function_data(node):
        params = []

        # positional args
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            params.append((arg.arg, safe_unparse(arg.annotation)))

        # *args
        if node.args.vararg:
            params.append(("*" + node.args.vararg.arg,
                           safe_unparse(node.args.vararg.annotation)))

        # **kwargs
        if node.args.kwarg:
            params.append(("**" + node.args.kwarg.arg,
                           safe_unparse(node.args.kwarg.annotation)))

        return_type = safe_unparse(node.returns)

        return params, return_type

    # ---------------- STYLE FORMATTERS ---------------- #

    def google_format(name, params, return_type):
        args_section = (
            "\n".join(f"    {p} ({t}): Description." for p, t in params)
            if params else "    None"
        )

        return f'''"""
Perform the {name} operation.

Args:
{args_section}

Returns:
    {return_type}: Description of return value.
"""'''

    def numpy_format(name, params, return_type):
        if params:
            param_lines = []
            for p, t in params:
                param_lines.append(f"{p} : {t}")
                param_lines.append("    Description.")
            params_block = "\n".join(param_lines)
        else:
            params_block = "None"

        return f'''"""
Perform the {name} operation.

Parameters
----------
{params_block}

Returns
-------
{return_type}
    Description of return value.
"""'''

    def rest_format(name, params, return_type):
        param_lines = []
        for p, t in params:
            param_lines.append(f":param {p}: Description.")
            param_lines.append(f":type {p}: {t}")

        params_block = "\n".join(param_lines)

        return f'''"""
Perform the {name} operation.

{params_block}

:return: Description of return value.
:rtype: {return_type}
"""'''

    # ---------------- FUNCTION ---------------- #

    if node_type == "function":
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params, return_type = extract_function_data(node)

                if style == "numpy":
                    return numpy_format(node.name, params, return_type)
                elif style == "rest":
                    return rest_format(node.name, params, return_type)
                else:
                    return google_format(node.name, params, return_type)

    # ---------------- CLASS ---------------- #

    if node_type == "class":
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return f'''"""
Represent the {node.name} class.

Provide structured data handling and related behaviors.
"""'''

    # ---------------- MODULE ---------------- #

    if node_type == "module":
        return '''"""
Provide module-level functionality.

Contain reusable components and definitions.
"""'''

    # ---------------- FINAL SAFETY ---------------- #

    return DEFAULT_DOCSTRING