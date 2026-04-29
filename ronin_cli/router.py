import os

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama


load_dotenv()

def get_langchain_llm():
    """Return a LangChain LLM/ChatModel based on environment configuration."""
    load_dotenv(override=True)
    
    model = os.getenv("MODEL", "gemini").lower()
    ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-coder")

    if model == "gemini":
        model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")
        api_key = os.getenv("GEMINI_API_KEY")
        return ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=0.1)

    if model == "ollama":
        return ChatOllama(model=ollama_model, temperature=0.1)

    # Fallback to a simple default to avoid hard crashes if MODEL is misconfigured
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    api_key = os.getenv("GEMINI_API_KEY")
    return ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=0.1)