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