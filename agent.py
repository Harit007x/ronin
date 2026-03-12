import json
from router import ModelRouter
from tools import TOOLS
from prompts import SYSTEM_PROMPT


class Agent:

    def __init__(self):
        self.model = ModelRouter()
        self.context = SYSTEM_PROMPT

    def step(self):

        response = self.model.generate(self.context)

        print("\nMODEL RESPONSE:\n", response)

        try:
            action = json.loads(response)
        except:
            self.context += "\nInvalid JSON response"
            return False

        if action["tool"] == "finish":
            print("\nTASK COMPLETE")
            return True

        tool = action["tool"]
        args = action.get("args", {})

        result = TOOLS[tool](**args)

        print("\nTOOL RESULT:\n", result)

        self.context += f"\nTool {tool} result:\n{result}"

        return False

    def run(self, task):

        self.context += f"\nUser task:\n{task}"

        for _ in range(10):

            done = self.step()

            if done:
                break