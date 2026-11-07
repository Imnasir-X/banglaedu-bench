"""Adapter interface and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Adapter(ABC):
    """Turns a chat message list into one completion string."""

    name: str = "adapter"

    @abstractmethod
    def generate(self, messages: list[dict], meta: dict | None = None) -> str:
        """Return the model's reply. `meta` carries item context, used only by mocks."""


def make_adapter(spec: str, **kwargs) -> Adapter:
    """Build an adapter from a spec string.

    mock-oracle | mock-random | mock-constant | mock-grounded | mock-judge
    openrouter:<model>        (needs OPENROUTER_API_KEY)
    ollama:<model>            (local, free: http://localhost:11434/v1)
    vllm:<model>              (local: http://localhost:8000/v1)
    openai-compat:<model>     (set --base-url and optionally --api-key-env)
    """
    from .mock import MOCKS
    from .openai_compat import PRESETS, OpenAICompatAdapter

    if spec in MOCKS:
        return MOCKS[spec](**kwargs)
    if ":" in spec:
        provider, model = spec.split(":", 1)
        if provider in PRESETS or provider == "openai-compat":
            return OpenAICompatAdapter.from_preset(provider, model, **kwargs)
    raise ValueError(f"unknown adapter spec '{spec}'")
