"""OpenAI-compatible chat completions over urllib (no third-party dependencies).

Works with OpenRouter, local Ollama (`ollama serve`, OpenAI API at /v1), vLLM,
llama.cpp server, LM Studio and any other /v1/chat/completions endpoint.
No paid key is needed for local Ollama/vLLM. OpenRouter needs an API key even
for its ':free' models.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from .base import Adapter

PRESETS = {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY"},
    "openai": {"base_url": "https://api.openai.com/v1", "key_env": "OPENAI_API_KEY"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY"},
    "ollama": {"base_url": "http://localhost:11434/v1", "key_env": None},
    "vllm": {"base_url": "http://localhost:8000/v1", "key_env": "VLLM_API_KEY"},
}
_KEY_REQUIRED = {"openrouter", "openai", "groq"}


class OpenAICompatAdapter(Adapter):
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        timeout: float = 120.0,
        retries: int = 3,
        extra_headers: dict | None = None,
        name: str | None = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retries = retries
        self.extra_headers = extra_headers or {}
        self.name = name or model

    @classmethod
    def from_preset(cls, provider: str, model: str, **kwargs) -> OpenAICompatAdapter:
        preset = PRESETS.get(provider, {"base_url": None, "key_env": None})
        base_url = kwargs.pop("base_url", None) or preset["base_url"]
        if not base_url:
            raise ValueError("openai-compat adapter needs --base-url")
        key_env = kwargs.pop("api_key_env", None) or preset["key_env"]
        api_key = os.environ.get(key_env) if key_env else None
        if provider in _KEY_REQUIRED and not api_key:
            raise RuntimeError(f"Set {key_env} to use {provider}")
        headers = {}
        if provider == "openrouter":
            headers = {"HTTP-Referer": "https://github.com/Imnasir-X", "X-Title": "BanglaEdu Bench"}
        return cls(
            model, base_url, api_key, extra_headers=headers, name=f"{provider}:{model}", **kwargs
        )

    def generate(self, messages, meta=None):
        body = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions", data=body, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"].get("content") or ""
            except urllib.error.HTTPError as exc:
                last_err = exc
                if exc.code not in (408, 429, 500, 502, 503, 504):
                    detail = exc.read().decode("utf-8", "replace")[:300]
                    raise RuntimeError(f"{self.name}: HTTP {exc.code}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
                last_err = exc
            time.sleep(min(2**attempt, 20))
        raise RuntimeError(f"{self.name}: request failed after retries: {last_err}")
