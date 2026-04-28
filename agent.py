import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt


from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from prompts import SYSTEM_PROMPT
from tools import TOOLS
from router import get_langchain_llm


load_dotenv()


class Agent:
    def __init__(self, model_display: str = "Unknown") -> None:
        self.llm = get_langchain_llm()
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]
        self.last_result = None
        self.model_display = model_display
        self.console = Console()
        self.tool_history = []  # Track (tool, args) to prevent loops
        self.current_stage = "PLANNING"
        self.has_verified = False  # Track if verification has been performed

    def display_step_header(self, thought: str = None):
        """Displays a rich header for the current step."""
        stage_colors = {
            "PLANNING": "bold magenta",
            "EXECUTION": "bold green",
            "VERIFICATION": "bold blue"
        }
        color = stage_colors.get(self.current_stage, "bold cyan")
        
        self.console.print(Panel(
            thought or "Thinking...",
            title=f"[{color}]{self.current_stage}[/{color}]",
            border_style=color
        ))

    def step(self) -> bool:
        """Single reasoning/tool step using the LLM and TOOLS."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=self.console
        ) as progress:
            progress.add_task(description=f"Model {self.model_display} is thinking...", total=None)
            start_time = time.time()
            response_msg = self.llm.invoke(self.messages)
            duration = time.time() - start_time

        # Support both message objects and plain strings
        if hasattr(response_msg, "content"):
            response = response_msg.content
            if isinstance(response, list):
                response = "".join(
                    [part.get("text", "") if isinstance(part, dict) else str(part) for part in response]
                )
            self.messages.append(AIMessage(content=response))
        else:
            response = str(response_msg)
            self.messages.append(AIMessage(content=response))

        clean_response = response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        elif clean_response.startswith("```"):
            clean_response = clean_response[3:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        try:
            action = json.loads(clean_response)
        except Exception:
            self.messages.append(HumanMessage(content="Invalid JSON response. Please provide a valid JSON object matching the requested schema."))
            self.console.print("[bold red]Error:[/] Invalid JSON returned by model.")
            return False

        # Update stage if present in response
        if "stage" in action:
            new_stage = action["stage"].upper()
            if new_stage == "EXECUTION" and self.current_stage != "EXECUTION":
                self.has_verified = False  # Reset if we backtrack
            self.current_stage = new_stage

        # Display thought if present
        self.display_step_header(action.get("thought"))

        if action.get("tool") == "finish":
            if self.current_stage == "VERIFICATION" and not self.has_verified:
                 self.messages.append(HumanMessage(content="Error: You must run a verification command (e.g., tests or build) in the VERIFICATION stage before finishing. If tests failed, you should move back to the EXECUTION stage to fix the issues."))
                 self.console.print("[bold orange3]Warning:[/] Agent tried to finish without successful verification.")
                 return False

            if "message" in action:
                self.console.print(Panel(action["message"], title="[bold green]TASK COMPLETE[/bold green]", border_style="green"))
            return True

        tool = action.get("tool")
        args = action.get("args", {}) or {}

        if tool not in TOOLS:
            self.messages.append(HumanMessage(content=f"Invalid tool requested: {tool}"))
            self.console.print(f"[bold red]Error:[/] Tool '{tool}' not found.")
            return False

        # Loop prevention
        tool_call = (tool, json.dumps(args, sort_keys=True))
        if tool_call in self.tool_history:
            msg = f"Error: You already called {tool} with these exact arguments. Please summarize your findings or try a different approach."
            self.messages.append(HumanMessage(content=msg))
            self.console.print(f"[bold orange3]Warning:[/] Loop detected for tool '{tool}'.")
            return False
        self.tool_history.append(tool_call)

        self.console.print(f"[bold yellow]Executing {tool}...[/bold yellow]")
        start_time = time.time()
        try:
            if tool == "run_command":
                cmd = args.get("cmd") or args.get("command")
                self.console.print(Panel(f"[bold white]{cmd}[/bold white]", title="[bold yellow]Pending Command Approval[/bold yellow]"))
                choice = Prompt.ask("Approve command?", choices=["Y", "N", "E", "y", "n", "e"], default="Y").upper()
                
                if choice == "N":
                    self.console.print("[bold red]Command rejected by user.[/bold red]")
                    result = "Error: Command rejected by user."
                elif choice == "E":
                    edited_cmd = Prompt.ask("Edit command")
                    args = {"cmd": edited_cmd}
                    self.console.print(f"[bold yellow]Executing edited command: {edited_cmd}[/bold yellow]")
                    result = TOOLS[tool](**args)
                else:
                    args = {"cmd": cmd}
                    result = TOOLS[tool](**args)

            else:
                result = TOOLS[tool](**args)

            duration = time.time() - start_time
            
            # If a command was run in verification stage, mark as verified if it succeeded
            if tool == "run_command" and self.current_stage == "VERIFICATION":
                if "exited with code 0" in str(result):
                    self.has_verified = True
                else:
                    self.has_verified = False
                    self.console.print("[bold red]Verification Failed:[/] Command returned non-zero exit code.")

            self.console.print(f"[dim gray]Done in {duration:.2f}s[/dim gray]")
            self.last_result = result
            self.messages.append(HumanMessage(content=f"Tool {tool} result:\n{result}"))
        except Exception as e:
            error_msg = f"Tool {tool} failed with error: {str(e)}"
            self.messages.append(HumanMessage(content=error_msg))
            self.console.print(f"[bold red]Tool Error:[/] {str(e)}")

        return False

    def run(self, task: str) -> None:
        self.messages.append(HumanMessage(content=f"User task:\n{task}"))

        for iteration in range(15):  # Increased iteration limit
            done = self.step()
            if done:
                break
        else:
            self.console.print("[bold red]Limit reached:[/] Agent stopped after 15 steps.")

        if self.last_result is not None:
             # Result is already printed in the 'finish' block if message is present
             pass
