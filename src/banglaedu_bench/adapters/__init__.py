"""Model adapters. `make_adapter("openrouter:<model>")`, `"ollama:<model>"`, `"mock-oracle"`..."""

from .base import Adapter, make_adapter

__all__ = ["Adapter", "make_adapter"]
