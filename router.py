import os
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "gemini")


class ModelRouter:

    def __init__(self):

        
        if MODEL == "gemini":
            self.client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )

    def generate(self, prompt):

        if MODEL == "gemini":

            response = self.client.models.generate_content(
                model=os.getenv("MODEL_NAME"),
                contents=prompt
            )

            if response.candidates:
                return response.candidates[0].content.parts[0].text

            return ""

        if MODEL == "ollama":

            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "deepseek-coder",
                    "prompt": prompt,
                    "stream": False
                }
            )

            return r.json()["response"]