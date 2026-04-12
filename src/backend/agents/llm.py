"""
ELI5 (What does this file do?):
Think of this file as our application's "brain connection manager".
Whenever our agents need to "think" using AI (the Large Language Model or LLM), they ask this file.
This file securely manages the key cards (API keys) that let us talk to the heavy-lifting AI (Groq cloud).
If one key card gets jammed because we are thinking too fast (rate limited), 
it seamlessly swaps to the next key card. And if the cloud is completely down, 
it has a backup plan to use a smaller, local brain on our own computer (Ollama).
"""
import os
import logging
import threading
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda

# Optional Ollama fallback — won't crash if not installed
try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Simple round-robin key picker
# ---------------------------------------------------------------------------

class _KeyPool:
    """Thread-safe round-robin pool for multiple Groq API keys."""

    def __init__(self):
        raw_multi = os.getenv("GROQ_API_KEYS", "").strip()
        raw_single = os.getenv("GROQ_API_KEY", "").strip()

        if raw_multi:
            self.keys = [k.strip() for k in raw_multi.split(",") if k.strip()]
        elif raw_single:
            self.keys = [raw_single]
        else:
            self.keys = []

        self._index = 0
        self._lock = threading.Lock()

    def next_key(self) -> str:
        with self._lock:
            key = self.keys[self._index % len(self.keys)]
            self._index = (self._index + 1) % len(self.keys)
            return key


_pool = _KeyPool()


def _is_rate_limit_error(exc: Exception) -> bool:
    err_str = str(exc).lower()
    if "429" in err_str or "rate" in err_str:
        return True
    if "ratelimit" in type(exc).__name__.lower():
        return True
    return False


def get_llm(temperature=0, json_mode=False):
    """
    Returns a LangChain LLM runnable.
    Primary: Groq cloud (llama-3.3-70b-versatile) with key rotation + retry
    Fallback: Local Ollama (qwen2.5:3b) if no Groq keys configured
    """
    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    if _pool.keys:
        # Sync invoke with retry across keys
        def _invoke(input_val, config=None):
            last_exc = None
            for attempt in range(len(_pool.keys)):
                key = _pool.next_key()
                llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=temperature,
                    api_key=key,
                    model_kwargs=model_kwargs,
                )
                try:
                    return llm.invoke(input_val, config=config)
                except Exception as exc:
                    if _is_rate_limit_error(exc):
                        logger.warning("Key %d/%d rate-limited, trying next...",
                                       attempt + 1, len(_pool.keys))
                        last_exc = exc
                        continue
                    raise
            raise RuntimeError(
                f"All {len(_pool.keys)} Groq key(s) rate-limited."
            ) from last_exc

        # Async invoke with retry across keys
        async def _ainvoke(input_val, config=None):
            last_exc = None
            for attempt in range(len(_pool.keys)):
                key = _pool.next_key()
                llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=temperature,
                    api_key=key,
                    model_kwargs=model_kwargs,
                )
                try:
                    return await llm.ainvoke(input_val, config=config)
                except Exception as exc:
                    if _is_rate_limit_error(exc):
                        logger.warning("Key %d/%d rate-limited, trying next...",
                                       attempt + 1, len(_pool.keys))
                        last_exc = exc
                        continue
                    raise
            raise RuntimeError(
                f"All {len(_pool.keys)} Groq key(s) rate-limited."
            ) from last_exc

        return RunnableLambda(func=_invoke, afunc=_ainvoke)

    # No Groq keys — try Ollama directly
    if OLLAMA_AVAILABLE:
        print("Warning: GROQ_API_KEY not found, using local Ollama.")
        if json_mode:
            return ChatOllama(model="qwen2.5:3b", format="json", temperature=temperature)
        return ChatOllama(model="qwen2.5:3b", temperature=temperature)

    raise RuntimeError("No LLM available: GROQ_API_KEY not set and langchain-ollama not installed.")
