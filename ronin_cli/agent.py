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

from .prompts import SYSTEM_PROMPT
from .tools import TOOLS
from .router import get_langchain_llm



load_dotenv()


class Agent:
    def __init__(self, model_display: str = "Unknown") -> None:
        self.llm = get_langchain_llm()
        self.messages = []
        self.last_result = None
        self.model_display = model_display
        self.console = Console()
        self.tool_history = []  # Track (tool, args) to prevent loops
        self.current_stage = "PLANNING"
        self.has_verified = False  # Track if verification has been performed
        self.total_input_tokens = 0
        self.total_output_tokens = 0


        import os
        self._history_file = os.path.join(os.getcwd(), ".ronin_history.json")
        self.load_history()

    def load_history(self):
        """Load conversation history from local working directory."""
        import os
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "sessions" in data:
                        active_id = data.get("active_session_id")
                        if active_id and active_id in data["sessions"]:
                            session = data["sessions"][active_id]
                            for item in session.get("messages", []):
                                if item.get("type") == "system":
                                    self.messages.append(SystemMessage(content=item["content"]))
                                elif item.get("type") == "human":
                                    self.messages.append(HumanMessage(content=item["content"]))
                                elif item.get("type") == "ai":
                                    self.messages.append(AIMessage(content=item["content"]))
                    else:
                        # Legacy backup format support
                        if isinstance(data, list):
                            for item in data:
                                if item.get("type") == "system":
                                    self.messages.append(SystemMessage(content=item["content"]))
                                elif item.get("type") == "human":
                                    self.messages.append(HumanMessage(content=item["content"]))
                                elif item.get("type") == "ai":
                                    self.messages.append(AIMessage(content=item["content"]))
            except Exception as e:
                self.console.print(f"[bold red]Warning:[/] Failed to load history ({e}).")

        # Guarantee system prompt at start
        if not self.messages or not isinstance(self.messages[0], SystemMessage):
            self.messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    def save_history(self):
        """Persist current conversation history onto local working directory."""
        msg_data = []
        first_human_prompt = ""
        for msg in self.messages:
            if isinstance(msg, SystemMessage):
                msg_data.append({"type": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                msg_data.append({"type": "human", "content": msg.content})
                if not first_human_prompt:
                    first_human_prompt = msg.content.replace("User task:\n", "").replace("\n", " ").replace("\r", " ").strip()

            elif isinstance(msg, AIMessage):
                msg_data.append({"type": "ai", "content": msg.content})

        # Load existing data to preserve concurrent logs
        data = {"active_session_id": "", "sessions": {}}
        import os
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict) or "sessions" not in data:
                        data = {"active_session_id": "legacy", "sessions": {"legacy": {"id": "legacy", "title": "Legacy Session", "messages": []}}}
            except Exception:
                pass

        active_id = data.get("active_session_id")
        if not active_id:
            import time
            active_id = f"session_{int(time.time())}"
            data["active_session_id"] = active_id

        if "sessions" not in data:
            data["sessions"] = {}

        # Save session payload
        data["sessions"][active_id] = {
            "id": active_id,
            "title": first_human_prompt if first_human_prompt else "Ongoing Task",
            "messages": msg_data
        }

        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.console.print(f"[bold red]Warning:[/] Failed to save history ({e}).")



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

    def get_pruned_messages(self):
        """Keep the system prompt, original user task, and a sliding window of recent interactions to limit token usage."""
        # Always keep SystemMessage (index 0) and the original HumanMessage User task (index 1)
        if len(self.messages) <= 12:
            return self.messages
            
        # Extract system and initial task
        base_context = self.messages[:2]
        
        # Keep the last 10 messages (5 interaction rounds) to maintain recent context 
        # without blowing up the payload size.
        recent_context = self.messages[-10:]
        
        return base_context + recent_context

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
            
            # Use pruned messages to save 70-80% on token costs for long tasks
            pruned_msgs = self.get_pruned_messages()
            response_msg = self.llm.invoke(pruned_msgs)
            
            duration = time.time() - start_time
            
            # Track token usage
            if hasattr(response_msg, "usage_metadata") and response_msg.usage_metadata:
                self.total_input_tokens += response_msg.usage_metadata.get("input_tokens", 0)
                self.total_output_tokens += response_msg.usage_metadata.get("output_tokens", 0)
            elif hasattr(response_msg, "response_metadata") and response_msg.response_metadata:
                meta = response_msg.response_metadata
                if "token_usage" in meta:
                    self.total_input_tokens += meta["token_usage"].get("prompt_tokens", 0)
                    self.total_output_tokens += meta["token_usage"].get("completion_tokens", 0)
                elif "usage" in meta:
                    self.total_input_tokens += meta["usage"].get("prompt_tokens", 0)
                    self.total_output_tokens += meta["usage"].get("completion_tokens", 0)


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
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        import re, os
        mentions = re.findall(r'@([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)', task)
        file_context = ""
        
        for mention in mentions:
            target_path = os.path.join(os.getcwd(), mention)
            if not os.path.exists(target_path):
                found_match = False
                base = os.path.basename(mention)
                for root, _, files in os.walk(os.getcwd()):
                    if base in files:
                        target_path = os.path.join(root, base)
                        found_match = True
                        break
                if not found_match:
                    continue

            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_context += f"\n\n--- Content of @{mention} ---\n{content}\n"
                self.console.print(f"[bold cyan]📎 Injected context for @{mention}[/bold cyan]")
            except Exception as e:
                self.console.print(f"[bold yellow]⚠️ Failed to load @{mention} content ({e})[/bold yellow]")

        full_prompt = f"User task:\n{task}"
        if file_context:
            full_prompt += file_context

        self.messages.append(HumanMessage(content=full_prompt))


        try:
            for iteration in range(15):  # Increased iteration limit
                done = self.step()
                if done:
                    break
            else:
                self.console.print("[bold red]Limit reached:[/] Agent stopped after 15 steps.")
        finally:
            self.save_history()
            
        self.console.print(f"\n[bold cyan]📊 Token Usage for this task:[/bold cyan]")
        self.console.print(f"   [bold]Input tokens:[/]  {self.total_input_tokens}")
        self.console.print(f"   [bold]Output tokens:[/] {self.total_output_tokens}")
        self.console.print(f"   [bold]Total tokens:[/]  {self.total_input_tokens + self.total_output_tokens}\n")

        if self.last_result is not None:

             # Result is already printed in the 'finish' block if message is present
             pass

