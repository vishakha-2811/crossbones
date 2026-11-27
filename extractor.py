import ast
import os
import sys

SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules", "build", "dist"}


def normalize(name):
    """parse_config -> PARSECONFIG. Returns None if not usable as an answer."""
    cleaned = name.replace("_", "")
    if not cleaned.isalpha() or not (4 <= len(cleaned) <= 15):
        return None
    return cleaned.upper()


def extract_symbols(repo_path):
    """Return a list of symbols found in the repo's .py files."""
    found = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(root, filename)
            rel = os.path.relpath(path, repo_path)
            try:
                with open(path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except (SyntaxError, UnicodeDecodeError):
                continue

            # the file itself
            found.append({"name": filename[:-3], "kind": "file", "file": rel,
                          "line": 1, "doc": ast.get_docstring(tree)})

            # functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    kind = "class" if isinstance(node, ast.ClassDef) else "function"
                    found.append({"name": node.name, "kind": kind, "file": rel,
                                  "line": node.lineno, "doc": ast.get_docstring(node)})

    # normalize and remove duplicates
    symbols = {}
    for s in found:
        answer = normalize(s["name"])
        if answer and answer not in symbols:
            s["answer"] = answer
            symbols[answer] = s
    return list(symbols.values())


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        print("Usage: python extractor.py <path to a folder>")
        print("That folder was not found. Check the path.")
        sys.exit(1)
    results = extract_symbols(sys.argv[1])
    print(f"Found {len(results)} usable symbols")
    for s in results:
        print(f'{s["answer"]:<16} {s["kind"]:<9} {s["file"]}:{s["line"]}')