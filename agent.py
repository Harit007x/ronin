import json
import time
from rich.console import Console

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

    def step(self) -> bool:
        """Single reasoning/tool step using the LLM and TOOLS."""
        self.console.print(f"\n[bold cyan][Thinking][/bold cyan] Calling model {self.model_display}...")
        start_time = time.time()
        response_msg = self.llm.invoke(self.messages)
        duration = time.time() - start_time
        self.console.print(f"[bold green][Done Thinking][/bold green] Model responded in {duration:.2f}s")

        # Support both message objects and plain strings
        if hasattr(response_msg, "content"):
            response = response_msg.content
            if isinstance(response, list):
                # LangChain can return a list of parts (dicts or strings) for complex models
                response = "".join(
                    [part.get("text", "") if isinstance(part, dict) else str(part) for part in response]
                )
            
            # Append the actual AIMessage back into the history correctly
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
            return False

        # Display thought if present
        if "thought" in action:
            self.console.print(f"[italic white]Thought: {action['thought']}[/italic white]")

        if action.get("tool") == "finish":
            if "message" in action:
                print("\nAGENT FINISHED WITH MESSAGE:\n", action["message"])
            return True

        tool = action.get("tool")
        args = action.get("args", {}) or {}

        if tool not in TOOLS:
            self.messages.append(HumanMessage(content=f"Invalid tool requested: {tool}"))
            return False

        # Loop prevention
        tool_call = (tool, json.dumps(args, sort_keys=True))
        if tool_call in self.tool_history:
            self.messages.append(HumanMessage(content=f"Error: You already called {tool} with these exact arguments. Please summarize your findings or try a different approach."))
            return False
        self.tool_history.append(tool_call)

        self.console.print(f"[bold yellow][Executing Tool][/bold yellow] {tool} with args: {args}...")
        start_time = time.time()
        result = TOOLS[tool](**args)
        duration = time.time() - start_time
        self.console.print(f"[bold green][Tool Finished][/bold green] {tool} took {duration:.2f}s")
        self.last_result = result

        self.messages.append(HumanMessage(content=f"Tool {tool} result:\n{result}"))

        return False

    def run(self, task: str) -> None:
        self.messages.append(HumanMessage(content=f"User task:\n{task}"))

        for _ in range(10):
            done = self.step()
            if done:
                break

        if self.last_result is not None:
            print("\nRESULT:\n", self.last_result)