import os
import subprocess
import time
from duckduckgo_search import DDGS
import re

def read_file(path):
    with open(path, "r") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)
    return "file written"


def list_files(path="."):
    return os.listdir(path)


def search_code(query, path=".", include_extension=None):
    """Search for a regex pattern in files within a directory, providing context."""
    results = []
    try:
        regex = re.compile(query, re.IGNORECASE)
    except re.error:
        return f"Invalid regex pattern: {query}"

    for root, _, files in os.walk(path):
        if any(ignored in root for ignored in ["venv", ".git", "__pycache__"]):
            continue
        for file in files:
            if include_extension and not file.endswith(include_extension):
                continue
            full_path = os.path.join(root, file)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        if regex.search(line):
                            # Provide context: one line before and after if possible
                            start = max(0, i - 2)
                            end = min(len(lines), i + 1)
                            match_context = []
                            for j in range(start, end):
                                prefix = "> " if j == i - 1 else "  "
                                match_context.append(f"{prefix}{j+1}: {lines[j].strip()}")
                            results.append(f"File: {full_path}\n" + "\n".join(match_context) + "\n")
            except Exception:
                continue
    return "\n".join(results[:20]) or "No matches found."


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
    blocked = ["rm -rf", "shutdown", "reboot"]
    if any(b in cmd for b in blocked):
        return "Error: blocked command"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=False)
        # Use 'replace' to handle unexpected characters on Windows
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        
        output = f"Command exited with code {result.returncode}\n"
        if stdout.strip():
            output += f"STDOUT:\n{stdout}\n"
        if stderr.strip():
            output += f"STDERR:\n{stderr}\n"
        
        return output or "Command completed with no output."
    except Exception as e:
        return f"Execution Error: {str(e)}"


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


def edit_file(path, target_content, replacement_content):
    """Replace a specific block of text in a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

    occurrences = content.count(target_content)
    if occurrences == 0:
        return f"Error: The target content was not found in {path}. Make sure you provide the EXACT strings, including whitespace."
    if occurrences > 1:
        return f"Error: The target content was found {occurrences} times in {path}. Please provide more unique context to identify the exact block to change."

    new_content = content.replace(target_content, replacement_content)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return f"Error writing file: {str(e)}"

    return f"Successfully updated {path}."


def bulk_edit(edits):
    """
    Apply multiple edits across one or more files.
    'edits' should be a list of dictionaries: {"path": "...", "target_content": "...", "replacement_content": "..."}
    """
    if not isinstance(edits, list):
        return "Error: 'edits' must be a list of edit objects."

    # First pass: Validate all edits (check if targets exist and are unique)
    file_contents = {}
    for i, edit in enumerate(edits):
        path = edit.get("path")
        target = edit.get("target_content")
        
        if not path or target is None:
            return f"Error in edit {i}: Missing 'path' or 'target_content'."
        
        # Cache file content to handle multiple edits to the same file in one pass
        if path not in file_contents:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    file_contents[path] = f.read()
            except Exception as e:
                return f"Error reading {path} for edit {i}: {str(e)}"
        
        occurrences = file_contents[path].count(target)
        if occurrences == 0:
            return f"Error in edit {i}: Target content not found in {path}."
        if occurrences > 1:
            return f"Error in edit {i}: Target content found {occurrences} times in {path}. Provide more context."

    # Second pass: Apply all edits to the cached contents
    updated_paths = set()
    for edit in edits:
        path = edit["path"]
        target = edit["target_content"]
        replacement = edit.get("replacement_content", "")
        file_contents[path] = file_contents[path].replace(target, replacement)
        updated_paths.add(path)

    # Third pass: Write updated contents back to disk
    try:
        for path in updated_paths:
            with open(path, "w", encoding="utf-8") as f:
                f.write(file_contents[path])
    except Exception as e:
        return f"Error writing files during bulk edit: {str(e)}"

    return f"Successfully applied {len(edits)} edits across {len(updated_paths)} files."


def _get_knowledge_dir():
    k_dir = os.path.join(".ronin", "knowledge")
    os.makedirs(k_dir, exist_ok=True)
    return k_dir


def store_knowledge(topic, content):
    """Store distilled knowledge about a topic in the knowledge base."""
    k_dir = _get_knowledge_dir()
    # Sanitize topic for filename
    safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '_', topic.lower())
    path = os.path.join(k_dir, f"{safe_topic}.md")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {topic}\n\n{content}")
        return f"Knowledge about '{topic}' stored successfully in {path}."
    except Exception as e:
        return f"Error storing knowledge: {str(e)}"


def list_knowledge():
    """List all topics in the knowledge base."""
    k_dir = _get_knowledge_dir()
    try:
        if not os.path.exists(k_dir):
            return "Knowledge base is currently empty."
        files = [f for f in os.listdir(k_dir) if f.endswith(".md")]
        topics = [f[:-3].replace("_", " ").title() for f in files]
        if not topics:
            return "Knowledge base is currently empty."
        return "Available knowledge topics:\n- " + "\n- ".join(topics)
    except Exception as e:
        return f"Error listing knowledge: {str(e)}"


def search_knowledge(query):
    """Search through existing knowledge items using a regex query."""
    k_dir = _get_knowledge_dir()
    results = []
    try:
        if not os.path.exists(k_dir):
             return f"No knowledge found matching query: {query}"
        regex = re.compile(query, re.IGNORECASE)
        for f in os.listdir(k_dir):
            if f.endswith(".md"):
                path = os.path.join(k_dir, f)
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if regex.search(content) or regex.search(f):
                        results.append(f"--- Topic: {f[:-3].replace('_', ' ').title()} ---\n{content}\n")
        
        if not results:
            return f"No knowledge found matching query: {query}"
        return "\n".join(results)
    except Exception as e:
        return f"Error searching knowledge: {str(e)}"


TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "bulk_edit": bulk_edit,
    "store_knowledge": store_knowledge,
    "list_knowledge": list_knowledge,
    "search_knowledge": search_knowledge,
    "list_files": list_files,
    "search_code": search_code,
    "get_project_structure": get_project_structure,
    "web_search": web_search,
    "run_command": run_command
}