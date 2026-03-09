"""Module for validating Python docstring compliance with PEP 257.

It provides functionality to run `pydocstyle` on Python files and report results.
"""
import google.generativeai as genai
import ast
import subprocess
import sys

def validate_pep257(filename: str):
    """Validate PEP 257 docstring compliance for a given file.

    Runs the `pydocstyle` tool to check for PEP 257 docstring violations in the specified Python file.

    Args:
        filename (str): The path to the Python file to validate.

    Returns:
        dict: A dictionary containing:
            - `passed` (bool): `True` if all docstrings are valid, `False` otherwise.
            - `message` (str): A success message if valid, or the `pydocstyle` output with errors if not.
    """
    print('\n Running PEP 257 (pydocstyle) validation...\n')
    result = subprocess.run([sys.executable, '-m', 'pydocstyle', filename], capture_output=True, text=True)
    output = (result.stdout + '\n' + result.stderr).strip()
    if not output:
        return {'passed': True, 'message': 'All docstrings are valid according to PEP 257'}
    return {'passed': False, 'message': output}