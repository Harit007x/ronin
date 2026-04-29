import os
import threading
import time

import typer

from dotenv import load_dotenv
from .agent import Agent


def load_config():
    """Load configuration from local, global, or installation .env files."""
    # 1. Load global fallback in ~/.ronin/.env
    global_config = os.path.expanduser("~/.ronin/.env")
    if os.path.exists(global_config):
        load_dotenv(global_config, override=True)

    # 2. Try local .env (current working directory) - takes precedence
    local_env = os.path.join(os.getcwd(), ".env")
    if os.path.exists(local_env):
        load_dotenv(local_env, override=True)

    # 3. Try installation folder fallback
    install_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(install_env) and not os.getenv("GEMINI_API_KEY"):
        load_dotenv(install_env, override=True)


def start_new_conversation():
    import os, json, time
    history_file = os.path.join(os.getcwd(), ".ronin_history.json")
    
    data = {"active_session_id": "", "sessions": {}}
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    session_id = f"session_{int(time.time())}"
    if "sessions" not in data:
        data["sessions"] = {}
        
    data["active_session_id"] = session_id
    data["sessions"][session_id] = {
        "id": session_id,
        "title": "Fresh Conversation",
        "messages": []
    }
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    from rich.console import Console
    Console().print("[bold green]Started a new conversation session successfully.[/bold green]")


def manage_conversations():
    import os, json, msvcrt, sys
    from rich.console import Console
    console = Console()
    
    history_file = os.path.join(os.getcwd(), ".ronin_history.json")
    if not os.path.exists(history_file):
        console.print("[bold yellow]No conversation history found in this workspace.[/bold yellow]")
        return
        
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Failed to read history:[/] {e}")
        return

    sessions = data.get("sessions", {})
    if not sessions:
        console.print("[bold yellow]No active conversation threads available.[/bold yellow]")
        return

    session_ids = list(sessions.keys())
    
    def get_title(sess):
        t = sess.get("title", "Empty").replace("User task:\n", "").replace("\n", " ").replace("\r", " ").strip()
        return t[:60] + "..." if len(t) > 60 else t

    idx = 0
    sys.stdout.write("\033[?25l")  # Hide cursor
    sys.stdout.flush()

    while True:
        sys.stdout.write("\033[s")  # Save cursor position
        console.print("[bold cyan]Manage Sessions (Up/Down to navigate, Enter to load, 'D' to delete, Esc to quit):[/bold cyan]")

        for i, s_id in enumerate(session_ids):
            sess = sessions[s_id]
            title = get_title(sess)
            is_active = (s_id == data.get("active_session_id"))
            active_marker = "[ACTIVE]" if is_active else ""
            
            if i == idx:
                sys.stdout.write(f"\033[2K\033[36m > {title} {active_marker}\033[0m\n")
            else:
                sys.stdout.write(f"\033[2K   {title} {active_marker}\n")

        sys.stdout.flush()

        key = msvcrt.getch()
        sys.stdout.write("\033[u")  # Restore cursor position
        sys.stdout.write("\033[J")  # Clear from cursor to bottom of screen

        if key == b'\r':  # Enter to select
            sys.stdout.write("\033[?25h")  # Show cursor
            sys.stdout.flush()
            data["active_session_id"] = session_ids[idx]
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            console.print(f"[bold green]Switched context to session: {get_title(sessions[session_ids[idx]])}[/bold green]")
            return
            
        elif key in (b'D', b'd'): # Delete
            deleted_id = session_ids.pop(idx)
            del sessions[deleted_id]
            
            if data.get("active_session_id") == deleted_id:
                data["active_session_id"] = session_ids[0] if session_ids else ""
                
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
            console.print(f"[bold orange3]Deleted session successfully.[/bold orange3]")
            if not session_ids:
                sys.stdout.write("\033[?25h")
                return
            idx = min(idx, len(session_ids) - 1)
            
        elif key == b'\x1b':  # ESC to quit
            sys.stdout.write("\033[?25h")  # Show cursor
            sys.stdout.flush()
            return
            
        elif key in (b'\xe0', b'\x00'):
            sub_key = msvcrt.getch()
            if sub_key == b'H':  # Up Arrow
                idx = (idx - 1) % len(session_ids)
            elif sub_key == b'P':  # Down Arrow
                idx = (idx + 1) % len(session_ids)


def run_agent(task: str = typer.Argument(..., help="Task for the coding agent")) -> None:
    """Run the coding agent on a single task."""
    load_config()

    if task in ["reset", "new"]:
        start_new_conversation()
        return

    if task == "history":
        manage_conversations()
        return

    if task == "current-model":
        from rich.prompt import Prompt
        from rich.console import Console
        console = Console()

        models = [
            "gemini-3-flash",
            "gemini-3.1-pro-preview",
            "gpt-oss"
        ]

        import msvcrt
        import sys

        console.print("[bold cyan]Available Models (Use Up/Down arrows and press Enter to select):[/bold cyan]")
        
        idx = 0
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.flush()

        while True:
            for i, m in enumerate(models):
                if i == idx:
                    sys.stdout.write(f"\033[36m > {m} \033[0m\n")
                else:
                    sys.stdout.write(f"   {m} \n")
            sys.stdout.flush()

            key = msvcrt.getch()
            sys.stdout.write(f"\033[{len(models)}A")

            if key == b'\r':
                sys.stdout.write(f"\033[{len(models)}B")
                sys.stdout.write("\033[?25h")  # Show cursor
                sys.stdout.flush()
                break
            elif key in (b'\xe0', b'\x00'):
                sub_key = msvcrt.getch()
                if sub_key == b'H':  # Up Arrow
                    idx = (idx - 1) % len(models)
                elif sub_key == b'P':  # Down Arrow
                    idx = (idx + 1) % len(models)

        selected_model = models[idx]

        updates = {}
        if selected_model == "gpt-oss":
            updates = {"MODEL": "ollama", "OLLAMA_MODEL": "gpt-oss"}
        else:
            updates = {"MODEL": "gemini", "MODEL_NAME": selected_model}

        local_env = os.path.join(os.getcwd(), ".env")
        global_env = os.path.expanduser("~/.ronin/.env")
        
        env_path = local_env
        if not os.path.exists(local_env) and os.path.exists(global_env):
            env_path = global_env

        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
            updated_keys = set()
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    if "=" in stripped:
                        key, _ = stripped.split("=", 1)
                        if key in updates:
                            new_lines.append(f"{key}={updates[key]}\n")
                            updated_keys.add(key)
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            for k, v in updates.items():
                if k not in updated_keys:
                    new_lines.append(f"{k}={v}\n")
            with open(env_path, "w") as f:
                f.writelines(new_lines)
        else:
            with open(local_env, "w") as f:
                for k, v in updates.items():
                    f.write(f"{k}={v}\n")

        console.print(f"[bold green]Successfully switched to {selected_model} and saved to {os.path.basename(env_path)}.[/bold green]")
        return

    model_env = os.getenv("MODEL", "gemini").lower()
    if model_env == "gemini":
        model_name = os.getenv("MODEL_NAME", "gemini")
        model_display = model_name
    elif model_env == "ollama":
        ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-coder")
        model_display = f"ollama/{ollama_model}"
    else:
        model_display = model_env

    agent = Agent(model_display=model_display)

    print("\n==============================")
    print(f"  USING MODEL -> {model_display}")
    print("==============================\n")

    try:
        agent.run(task)
    finally:
        pass


def main():
    typer.run(run_agent)


if __name__ == "__main__":
    main()