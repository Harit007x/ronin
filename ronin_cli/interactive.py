import os
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion

from .agent import Agent

class FileCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Find if user is currently typing an '@' mention
        last_word = ""
        # Split text by spaces and check the very last token
        tokens = text.split()
        if tokens:
            candidate = tokens[-1]
            if candidate.startswith('@'):
                last_word = candidate

        if not last_word:
            return

        query = last_word[1:]
        cwd = os.getcwd()
        
        try:
            for root, dirs, files in os.walk(cwd):
                # Prune common heavy directories
                for ignore_dir in ['.git', 'venv', '__pycache__', 'node_modules', '.venv', 'env']:
                    if ignore_dir in dirs:
                        dirs.remove(ignore_dir)
                        
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), cwd)
                    rel_path = rel_path.replace("\\", "/")
                    
                    if query.lower() in rel_path.lower() or not query:
                        yield Completion(
                            f"@{rel_path}", 
                            start_position=-len(last_word),
                            display=f"@{rel_path}"
                        )
        except Exception:
            pass

def run_interactive_shell():
    from rich.console import Console
    console = Console()
    
    # Resolve model info
    model_env = os.getenv("MODEL", "gemini").lower()
    if model_env == "gemini":
        model_display = os.getenv("MODEL_NAME", "gemini")
    elif model_env == "ollama":
        model_display = f"ollama/{os.getenv('OLLAMA_MODEL', 'deepseek-coder')}"
    else:
        model_display = model_env

    console.print(f"\n[bold magenta]🚀 Booting Interactive REPL Session for ronin-cli[/bold magenta]")
    console.print(f"[dim]Active Model:[/] [bold cyan]{model_display}[/bold cyan]")
    console.print("[dim]Type prompt below. Use '@' for file suggestions. Type 'exit' to quit.[/dim]\n")

    agent = Agent(model_display=model_display)
    session = PromptSession(completer=FileCompleter())
    
    while True:
        try:
            user_input = session.prompt("ronin ❯ ")
            clean_input = user_input.strip()
            
            if clean_input == "":
                continue
            if clean_input.lower() in ["exit", "quit", ":q"]:
                console.print("[yellow]Exiting interactive session.[/yellow]")
                break
                
            if clean_input.lower() in ["clear", "cls"]:
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

                
            if clean_input == "history":
                from .cli import manage_conversations
                manage_conversations()
                continue
                
            if clean_input == "current-model":
                from .cli import switch_model
                switch_model()
                
                # Update model display dynamically
                model_env = os.getenv("MODEL", "gemini").lower()
                if model_env == "gemini":
                    model_display = os.getenv("MODEL_NAME", "gemini")
                elif model_env == "ollama":
                    model_display = f"ollama/{os.getenv('OLLAMA_MODEL', 'deepseek-coder')}"
                else:
                    model_display = model_env
                    
                agent = Agent(model_display=model_display)
                continue
                
            if clean_input in ["reset", "new"]:
                from .cli import start_new_conversation
                start_new_conversation()
                agent = Agent(model_display=model_display)
                continue

            console.print(f"\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]\n")
            agent.run(user_input)
            console.print(f"\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]\n")

            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'exit' or Ctrl-D to leave.[/yellow]")
            continue
        except EOFError:
            break
