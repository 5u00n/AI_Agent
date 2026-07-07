with open("agent.py") as f:
    text = f.read()

import ast
try:
    ast.parse(text)
    print("Parsed successfully!")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno}, offset {e.offset}")
    print(e.text)
    print(" " * (e.offset - 1) + "^")
