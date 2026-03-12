import os
import threading
import time

import typer
from agent import Agent

app = typer.Typer()


@app.command()
def run(task: str):

    agent = Agent()

    model_env = os.getenv("MODEL", "gemini").lower()
    if model_env == "gemini":
        model_name = os.getenv("MODEL_NAME", "gemini")
        model_display = f"Gemini model: {model_name}"
    elif model_env == "ollama":
        ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-coder")
        model_display = f"Ollama model: {ollama_model}"
    else:
        model_display = f"Model: {model_env}"

    print("\n==============================")
    print(f"  USING MODEL -> {model_display}")
    print("==============================\n")

    stop_spinner = False

    def spinner():
        symbols = ["|", "/", "-", "\\"]
        idx = 0
        while not stop_spinner:
            print(f"\rProcessing {symbols[idx % len(symbols)]}", end="", flush=True)
            idx += 1
            time.sleep(0.1)
        print("\rProcessing done  ", flush=True)

    t = threading.Thread(target=spinner, daemon=True)
    t.start()

    try:
        agent.run(task)
    finally:
        stop_spinner = True
        t.join()


if __name__ == "__main__":
    app()