import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq

# Optional Ollama fallback — won't crash if not installed
try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


def get_llm(temperature=0, json_mode=False):
    """
    Returns a LangChain LLM runnable.
    Primary: Groq cloud (llama-3.3-70b-versatile)
    Fallback: Local Ollama (qwen2.5:3b) if installed
    """
    api_key = os.getenv("GROQ_API_KEY")

    # Build Groq primary
    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    if api_key:
        primary_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            api_key=api_key,
            model_kwargs=model_kwargs,
        )

        # Attach Ollama fallback if available
        if OLLAMA_AVAILABLE:
            if json_mode:
                fallback_llm = ChatOllama(model="qwen2.5:3b", format="json", temperature=temperature)
            else:
                fallback_llm = ChatOllama(model="qwen2.5:3b", temperature=temperature)
            return primary_llm.with_fallbacks([fallback_llm])

        return primary_llm

    # No Groq key — try Ollama directly
    if OLLAMA_AVAILABLE:
        print("Warning: GROQ_API_KEY not found, using local Ollama.")
        if json_mode:
            return ChatOllama(model="qwen2.5:3b", format="json", temperature=temperature)
        return ChatOllama(model="qwen2.5:3b", temperature=temperature)

    raise RuntimeError("No LLM available: GROQ_API_KEY not set and langchain-ollama not installed.")
