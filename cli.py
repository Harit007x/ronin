import os
import threading
import time

import typer

from agent import Agent


def main(task: str = typer.Argument(..., help="Task for the coding agent")) -> None:
    """Run the coding agent on a single task."""

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


if __name__ == "__main__":
    typer.run(main)