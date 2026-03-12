import os
import subprocess
import time
from ddgs import DDGS

def read_file(path):
    with open(path, "r") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)
    return "file written"


def list_files(path="."):
    return os.listdir(path)


def search_code(query, path="."):
    """Search for a string in all files within a directory."""
    results = []
    for root, _, files in os.walk(path):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            full_path = os.path.join(root, file)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            results.append(f"{full_path}:{i}: {line.strip()}")
            except Exception:
                continue
    return "\n".join(results[:50]) or "No matches found."


def get_project_structure(path="."):
    """Return a simplified directory tree of the project."""
    tree = []
    for root, dirs, files in os.walk(path):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        level = root.replace(path, "").count(os.sep)
        indent = " " * 4 * level
        tree.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = " " * 4 * (level + 1)
        for f in files:
            tree.append(f"{sub_indent}{f}")
    return "\n".join(tree)


def run_command(cmd):
    # ... previous implementation ...
    blocked = ["rm -rf", "shutdown", "reboot"]
    if any(b in cmd for b in blocked):
        return "blocked command"

    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout.decode()


def web_search(query):
    """Search the web for information using DuckDuckGo with a timeout."""
    results = []
    try:
        with DDGS(timeout=10) as ddgs:
            # The new ddgs library returns a list of dictionaries
            search_results = ddgs.text(query, max_results=5)
            for r in search_results:
                results.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}\n")
    except Exception as e:
        return f"Search failed or timed out: {str(e)}"
    return "\n".join(results) or "No results found."


TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "search_code": search_code,
    "get_project_structure": get_project_structure,
    "web_search": web_search,
    "run_command": run_command
}