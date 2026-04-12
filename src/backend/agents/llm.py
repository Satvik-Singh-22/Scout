"""
Banquoite — LLM Provider with API Key Rotation

Supports multiple Groq API keys for round-robin rotation to avoid
rate-limit (429) errors during demos and presentations.

Configuration:
    GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3   (preferred, comma-separated)
    GROQ_API_KEY=gsk_single_key                  (backward compatible)
"""

import os
import time
import logging
import threading
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq

# Optional Ollama fallback — won't crash if not installed
try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Key Rotation Engine
# ---------------------------------------------------------------------------

COOLDOWN_SECONDS = 40  # Per-key cooldown after a 429


class _KeyState:
    """Tracks usage stats and cooldown for a single API key."""

    __slots__ = ("key", "calls_made", "cooldown_until")

    def __init__(self, key: str):
        self.key = key
        self.calls_made = 0
        self.cooldown_until: float = 0.0  # epoch timestamp

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until

    @property
    def status(self) -> str:
        return "available" if self.is_available else "cooldown"

    def mark_rate_limited(self):
        self.cooldown_until = time.time() + COOLDOWN_SECONDS

    def to_dict(self, index: int) -> dict:
        d = {
            "index": index,
            "status": self.status,
            "calls_made": self.calls_made,
        }
        if not self.is_available:
            remaining = max(0, int(self.cooldown_until - time.time()))
            d["cooldown_remaining_s"] = remaining
        return d


class GroqKeyRotator:
    """
    Thread-safe round-robin key pool for Groq API keys.

    On a 429 error the current key enters a 40-second cooldown and the
    request is retried transparently with the next available key.
    """

    def __init__(self):
        self._keys: list[_KeyState] = []
        self._index: int = 0
        self._lock = threading.Lock()
        self._load_keys()

    # -- bootstrap --------------------------------------------------------

    def _load_keys(self):
        raw_multi = os.getenv("GROQ_API_KEYS", "").strip()
        raw_single = os.getenv("GROQ_API_KEY", "").strip()

        if raw_multi:
            keys = [k.strip() for k in raw_multi.split(",") if k.strip()]
        elif raw_single:
            keys = [raw_single]
        else:
            keys = []

        self._keys = [_KeyState(k) for k in keys]
        if self._keys:
            logger.info("Groq key pool initialised with %d key(s)", len(self._keys))
        else:
            logger.warning("No Groq API keys configured")

    # -- selection --------------------------------------------------------

    @property
    def pool_size(self) -> int:
        return len(self._keys)

    @property
    def has_keys(self) -> bool:
        return len(self._keys) > 0

    def _next_available_key(self) -> Optional[_KeyState]:
        """Return the next available key (round-robin), or None."""
        n = len(self._keys)
        for _ in range(n):
            ks = self._keys[self._index % n]
            self._index = (self._index + 1) % n
            if ks.is_available:
                return ks
        return None

    def get_key(self) -> Optional[_KeyState]:
        with self._lock:
            return self._next_available_key()

    def mark_rate_limited(self, key_state: _KeyState):
        with self._lock:
            key_state.mark_rate_limited()
            # Identify key index for logging
            idx = next(
                (i for i, ks in enumerate(self._keys) if ks is key_state), -1
            )
            avail = sum(1 for ks in self._keys if ks.is_available)
            logger.warning(
                "Key [%d/%d] rate-limited → cooling down %ds  |  Pool: %d/%d available",
                idx + 1, len(self._keys), COOLDOWN_SECONDS,
                avail, len(self._keys),
            )

    # -- health -----------------------------------------------------------

    def health(self) -> dict:
        with self._lock:
            available = sum(1 for ks in self._keys if ks.is_available)
            return {
                "total_keys": len(self._keys),
                "available_keys": available,
                "current_index": self._index,
                "cooldown_seconds": COOLDOWN_SECONDS,
                "keys": [ks.to_dict(i) for i, ks in enumerate(self._keys)],
                "fallback": "ollama" if OLLAMA_AVAILABLE else "none",
            }


# Module-level singleton
_rotator = GroqKeyRotator()


def get_rotator() -> GroqKeyRotator:
    """Expose the rotator singleton (used by the health endpoint)."""
    return _rotator


# ---------------------------------------------------------------------------
# Rate-limit-aware ChatGroq wrapper
# ---------------------------------------------------------------------------

class _RotatingGroqLLM:
    """
    Drop-in proxy around ChatGroq that intercepts 429 errors and
    retries with the next key from the pool.  Implements the Runnable
    interface methods that LangChain chains actually call.
    """

    def __init__(self, rotator: GroqKeyRotator, temperature: float, model_kwargs: dict):
        self._rotator = rotator
        self._temperature = temperature
        self._model_kwargs = model_kwargs
        self._model_name = "llama-3.3-70b-versatile"

    def _make_llm(self, key_state: _KeyState) -> ChatGroq:
        key_state.calls_made += 1
        idx = next(
            (i for i, ks in enumerate(self._rotator._keys) if ks is key_state), -1
        )
        logger.info("Using Groq key [%d/%d]", idx + 1, self._rotator.pool_size)
        return ChatGroq(
            model=self._model_name,
            temperature=self._temperature,
            api_key=key_state.key,
            model_kwargs=self._model_kwargs,
        )

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        """Detect Groq 429 errors from various exception types."""
        err_str = str(exc).lower()
        if "429" in err_str or "rate" in err_str or "rate_limit" in err_str:
            return True
        # groq SDK raises groq.RateLimitError
        exc_type = type(exc).__name__
        if "ratelimit" in exc_type.lower():
            return True
        return False

    def _call_with_rotation(self, method_name: str, *args, **kwargs):
        """Try each key in the pool once; raise on complete exhaustion."""
        tried = 0
        last_exc = None

        while tried < self._rotator.pool_size:
            ks = self._rotator.get_key()
            if ks is None:
                break  # all keys cooling down
            llm = self._make_llm(ks)
            try:
                return getattr(llm, method_name)(*args, **kwargs)
            except Exception as exc:
                if self._is_rate_limit_error(exc):
                    self._rotator.mark_rate_limited(ks)
                    last_exc = exc
                    tried += 1
                    continue
                raise  # non-rate-limit error, propagate immediately

        raise RuntimeError(
            f"All {self._rotator.pool_size} Groq API key(s) are rate-limited. "
            f"Please wait ~{COOLDOWN_SECONDS}s and retry."
        ) from last_exc

    async def _acall_with_rotation(self, method_name: str, *args, **kwargs):
        """Async version of _call_with_rotation."""
        tried = 0
        last_exc = None

        while tried < self._rotator.pool_size:
            ks = self._rotator.get_key()
            if ks is None:
                break
            llm = self._make_llm(ks)
            try:
                return await getattr(llm, method_name)(*args, **kwargs)
            except Exception as exc:
                if self._is_rate_limit_error(exc):
                    self._rotator.mark_rate_limited(ks)
                    last_exc = exc
                    tried += 1
                    continue
                raise

        raise RuntimeError(
            f"All {self._rotator.pool_size} Groq API key(s) are rate-limited. "
            f"Please wait ~{COOLDOWN_SECONDS}s and retry."
        ) from last_exc

    # -- LangChain Runnable interface -------------------------------------

    def invoke(self, *args, **kwargs):
        return self._call_with_rotation("invoke", *args, **kwargs)

    async def ainvoke(self, *args, **kwargs):
        return await self._acall_with_rotation("ainvoke", *args, **kwargs)

    def batch(self, *args, **kwargs):
        return self._call_with_rotation("batch", *args, **kwargs)

    async def abatch(self, *args, **kwargs):
        return await self._acall_with_rotation("abatch", *args, **kwargs)

    def stream(self, *args, **kwargs):
        return self._call_with_rotation("stream", *args, **kwargs)

    async def astream(self, *args, **kwargs):
        return await self._acall_with_rotation("astream", *args, **kwargs)

    # Pipe / chain support
    def __or__(self, other):
        """Support  prompt | llm  syntax."""
        from langchain_core.runnables import RunnableSequence
        return RunnableSequence(first=self, last=other)

    def __ror__(self, other):
        """Support  prompt | llm  syntax (right-hand side)."""
        from langchain_core.runnables import RunnableSequence
        return RunnableSequence(first=other, last=self)

    def with_fallbacks(self, fallbacks):
        """Wrap in LangChain's RunnableWithFallbacks."""
        from langchain_core.runnables import RunnableWithFallbacks
        return RunnableWithFallbacks(runnable=self, fallbacks=fallbacks)

    # Make it look like a proper LangChain object for introspection
    @property
    def InputType(self):
        dummy = ChatGroq(model=self._model_name, api_key="dummy")
        return dummy.InputType

    @property
    def OutputType(self):
        dummy = ChatGroq(model=self._model_name, api_key="dummy")
        return dummy.OutputType


# ---------------------------------------------------------------------------
# Public API  (unchanged signature)
# ---------------------------------------------------------------------------

def get_llm(temperature=0, json_mode=False):
    """
    Returns a LangChain LLM runnable.

    Primary : Groq cloud (llama-3.3-70b-versatile) with key rotation
    Fallback: Local Ollama (qwen2.5:3b) if installed and Groq unavailable
    """
    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    if _rotator.has_keys:
        primary_llm = _RotatingGroqLLM(_rotator, temperature, model_kwargs)

        # Attach Ollama fallback for NON-rate-limit failures (e.g. network down)
        if OLLAMA_AVAILABLE:
            if json_mode:
                fallback_llm = ChatOllama(model="qwen2.5:3b", format="json", temperature=temperature)
            else:
                fallback_llm = ChatOllama(model="qwen2.5:3b", temperature=temperature)
            return primary_llm.with_fallbacks([fallback_llm])

        return primary_llm

    # No Groq keys — try Ollama directly
    if OLLAMA_AVAILABLE:
        print("Warning: No Groq API keys found, using local Ollama.")
        if json_mode:
            return ChatOllama(model="qwen2.5:3b", format="json", temperature=temperature)
        return ChatOllama(model="qwen2.5:3b", temperature=temperature)

    raise RuntimeError("No LLM available: GROQ_API_KEY(S) not set and langchain-ollama not installed.")
