"""Minimal MCP client over stdio (newline-delimited JSON-RPC 2.0), stdlib only.

Enough to call the nctb-mcp server's tools (get_topic, search_curriculum, ...)
from the harness: initialize -> notifications/initialized -> tools/call.
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import time

PROTOCOL_VERSION = "2025-06-18"


class MCPError(RuntimeError):
    pass


class StdioMCPClient:
    def __init__(self, command: list[str], timeout: float = 30.0, env: dict | None = None):
        self.command = command
        self.timeout = timeout
        self._id = 0
        self.proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env={**os.environ, **(env or {})},
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.server_info = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "banglaedu-bench", "version": "0.1.0"},
            },
        )
        self._notify("notifications/initialized", {})

    # -- transport -----------------------------------------------------------
    def _send(self, msg: dict) -> None:
        if self.proc.stdin is None or self.proc.poll() is not None:
            raise MCPError("MCP server is not running")
        self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def _notify(self, method: str, params: dict) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _request(self, method: str, params: dict) -> dict:
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        assert self.proc.stdout is not None
        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.proc.stdout], [], [], 0.2)
            if not ready:
                if self.proc.poll() is not None:
                    raise MCPError("MCP server exited")
                continue
            line = self.proc.stdout.readline()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue  # servers may log to stdout; ignore non-JSON lines
            if msg.get("id") != rid:
                continue  # notifications or unrelated responses
            if "error" in msg:
                raise MCPError(f"{method}: {msg['error']}")
            return msg.get("result", {})
        raise MCPError(f"{method}: timed out after {self.timeout}s")

    # -- API -----------------------------------------------------------------
    def list_tools(self) -> list[dict]:
        return self._request("tools/list", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool and return its text content joined (structured content as JSON)."""
        res = self._request("tools/call", {"name": name, "arguments": arguments})
        if res.get("isError"):
            raise MCPError(f"tool {name} returned an error: {res.get('content')}")
        parts = []
        for c in res.get("content", []):
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
        if not parts and "structuredContent" in res:
            parts.append(json.dumps(res["structuredContent"], ensure_ascii=False))
        return "\n".join(parts)

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
