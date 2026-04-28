import os
import threading
import time

import typer

from dotenv import load_dotenv
from agent import Agent


def load_config():
    """Load configuration from local or global .env file."""
    # 1. Try local .env (current working directory)
    load_dotenv(os.path.join(os.getcwd(), ".env"))
    
    # 2. Fallback to global .env if critical vars are missing
    if not os.getenv("MODEL") and not os.getenv("GEMINI_API_KEY"):
        global_config = os.path.expanduser("~/.ronin/.env")
        if os.path.exists(global_config):
            load_dotenv(global_config)


def run_agent(task: str = typer.Argument(..., help="Task for the coding agent")) -> None:
    """Run the coding agent on a single task."""
    load_config()

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

        console.print("[bold cyan]Available Models (Use ↑/↓ arrows and press Enter to select):[/bold cyan]")
        
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
        if selected_model == "gemini-3-flash":
            updates = {"MODEL": "gemini", "MODEL_NAME": "gemini-3-flash"}
        elif selected_model == "gemini-3.1-pro-preview":
            updates = {"MODEL": "gemini", "MODEL_NAME": "gemini-3.1-pro-preview"}
        elif selected_model == "gpt-oss":
            updates = {"MODEL": "ollama", "OLLAMA_MODEL": "gpt-oss"}

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


    # Resolve model info for display
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