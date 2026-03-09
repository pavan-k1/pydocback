import google.generativeai as genai
import ast
import subprocess
import sys







def validate_pep257(filename: str):
    print("\n Running PEP 257 (pydocstyle) validation...\n")

    result = subprocess.run(
        [sys.executable, "-m", "pydocstyle", filename],
        capture_output=True,
        text=True
    )

    output = (result.stdout + "\n" + result.stderr).strip()

    if not output:
        return {
            "passed": True,
            "message": "All docstrings are valid according to PEP 257"
        }

    return {
        "passed": False,
        "message": output
    }