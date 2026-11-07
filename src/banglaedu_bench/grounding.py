"""Curriculum grounding for the with-MCP vs without-MCP comparison.

Modes
-----
none    no curriculum context (baseline).
search  retrieve by the question text (search_curriculum). This is the fair,
        headline "with MCP" condition: the model gets only what a student could
        look up from the question.
topic   fetch by the item's topic_id (get_topic). Leaks the topic label, so it is
        an upper bound, reported separately.

Sources
-------
* a live nctb-mcp server over stdio (`--mcp-command "npx -y nctb-mcp"`), or
* the JSON bundle nctb-mcp ships for offline use (`--mcp-bundle path.json`).

Grounding is injected into the prompt (retrieval-augmented), so every model is
compared the same way whether or not it supports tool calling.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .mcp_client import StdioMCPClient
from .normalize import normalize_text

MODES = ("none", "search", "topic")
MAX_CHARS = 2500


class Grounding:
    mode = "none"
    source = "none"

    def context(self, item: dict, query: str) -> str:
        return ""

    def close(self) -> None:
        pass


class NoGrounding(Grounding):
    pass


# ----------------------------------------------------------------- bundle
_TEXT_KEYS = ("text", "content", "summary", "body", "description", "text_bn")
_TITLE_KEYS = ("title_bn", "title", "name", "heading")
_ID_KEYS = ("topic_id", "id")


def _records(obj, out: list[dict]) -> None:
    """Flatten any reasonable nested bundle into {id, title, text} records."""
    if isinstance(obj, list):
        for x in obj:
            _records(x, out)
    elif isinstance(obj, dict):
        rid = next((obj[k] for k in _ID_KEYS if isinstance(obj.get(k), str)), None)
        title = next((obj[k] for k in _TITLE_KEYS if isinstance(obj.get(k), str)), "")
        text_parts = [obj[k] for k in _TEXT_KEYS if isinstance(obj.get(k), str)]
        for k in ("objectives", "learning_objectives", "key_points"):
            v = obj.get(k)
            if isinstance(v, list):
                text_parts += [
                    x if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in v
                ]
        if rid and (title or text_parts):
            out.append({"id": rid, "title": title, "text": "\n".join(text_parts)})
        for v in obj.values():
            if isinstance(v, (list, dict)):
                _records(v, out)


def _title(v) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, dict):  # e.g. {"bn": ..., "en": ...}
        return " / ".join(str(x) for x in v.values() if isinstance(x, str))
    return ""


def _nctb_data_records(data: dict) -> list[dict]:
    """Records from an nctb-data bundle (structure + objectives only, no body text).

    Each topic record carries its section number and title, its chapter title and the
    chapter's learning objectives: exactly what the nctb-mcp tools can return.
    """
    chapters = {c["id"]: c for c in data.get("chapters", [])}
    objectives: dict[str, list[str]] = {}
    for o in data.get("objectives", []):
        objectives.setdefault(o.get("chapter_id", ""), []).append(_title(o.get("text")))
    out = []
    for t in data.get("topics", []):
        ch = chapters.get(t.get("chapter_id"), {})
        lines = [
            f"অধ্যায়: {_title(ch.get('title'))}",
            f"অনুচ্ছেদ {t.get('number', '')}: {_title(t.get('title'))} {_title(t.get('title_alt'))}".strip(),
        ]
        objs = objectives.get(t.get("chapter_id", ""), [])
        if objs:
            lines.append("শিখনফল: " + "; ".join(objs))
        out.append({"id": t["id"], "title": _title(t.get("title")), "text": "\n".join(lines)})
    return out


def _char_ngrams(s: str, n: int = 3) -> set[str]:
    s = normalize_text(s).replace(" ", "")
    return {s[i : i + n] for i in range(max(0, len(s) - n + 1))}


class BundleGrounding(Grounding):
    source = "bundle"

    def __init__(self, path: str | Path, mode: str, top_k: int = 3, id_map: dict | None = None):
        if mode not in ("search", "topic"):
            raise ValueError("bundle grounding mode must be search or topic")
        self.mode = mode
        self.top_k = top_k
        self.id_map = id_map or {}
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.records: list[dict] = []
        if isinstance(data, dict) and data.get("dataset") == "nctb-data":
            self.records = _nctb_data_records(data)
        else:
            _records(data, self.records)
        if not self.records:
            raise ValueError(f"no topic records with ids found in {path}")
        self._title_grams = [_char_ngrams(r["title"]) for r in self.records]
        self._grams = [_char_ngrams(r["title"] + " " + r["text"]) for r in self.records]

    def _fmt(self, recs: list[dict]) -> str:
        blocks = [f"[{r['id']}] {r['title']}\n{r['text']}".strip() for r in recs]
        return "\n\n".join(blocks)[:MAX_CHARS]

    def context(self, item: dict, query: str) -> str:
        if self.mode == "topic":
            tid = self.id_map.get(item["topic_id"], item["topic_id"])
            recs = [r for r in self.records if r["id"] == tid]
            if not recs:  # fall back to the chapter prefix
                prefix = re.sub(r":t\d+$", "", tid)
                recs = [r for r in self.records if r["id"].startswith(prefix)][: self.top_k]
            return self._fmt(recs)
        # Offline approximation of search_curriculum: title matches count double,
        # and Jaccard (not raw overlap) keeps long objective lists from dominating.
        q = _char_ngrams(query)

        def jac(a: set, b: set) -> float:
            return len(a & b) / (len(a | b) or 1)

        scored = sorted(
            (
                (2 * jac(q, tg) + jac(q, g), i)
                for i, (tg, g) in enumerate(zip(self._title_grams, self._grams, strict=False))
            ),
            reverse=True,
        )
        recs = [self.records[i] for s, i in scored[: self.top_k] if s > 0]
        return self._fmt(recs)


# ----------------------------------------------------------------- live MCP
class MCPGrounding(Grounding):
    source = "mcp"

    def __init__(
        self,
        command: list[str],
        mode: str,
        topic_tool: str = "get_topic",
        topic_arg: str = "topic_id",
        search_tool: str = "search_curriculum",
        search_arg: str = "query",
        id_map: dict | None = None,
    ):
        if mode not in ("search", "topic"):
            raise ValueError("MCP grounding mode must be search or topic")
        self.mode = mode
        self.client = StdioMCPClient(command)
        self.topic_tool, self.topic_arg = topic_tool, topic_arg
        self.search_tool, self.search_arg = search_tool, search_arg
        self.id_map = id_map or {}
        self._cache: dict[str, str] = {}

    def context(self, item: dict, query: str) -> str:
        if self.mode == "topic":
            tid = self.id_map.get(item["topic_id"], item["topic_id"])
            key, tool, args = f"t:{tid}", self.topic_tool, {self.topic_arg: tid}
        else:
            key, tool, args = f"s:{query}", self.search_tool, {self.search_arg: query}
        if key not in self._cache:
            self._cache[key] = self.client.call_tool(tool, args)[:MAX_CHARS]
        return self._cache[key]

    def close(self) -> None:
        self.client.close()


def load_id_map(path: str | Path | None) -> dict:
    """Map this benchmark's provisional topic ids to the shared nctb-mcp ids (CSV)."""
    if not path:
        return {}
    import csv

    out = {}
    with Path(path).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            shared = (row.get("shared_topic_id") or "").strip()
            if shared:
                out[row["topic_id"]] = shared
    return out


def make_grounding(
    mode: str,
    bundle: str | None = None,
    mcp_command: list[str] | None = None,
    id_map_path: str | None = None,
    **tool_names,
) -> Grounding:
    if mode == "none":
        return NoGrounding()
    if mode not in MODES:
        raise ValueError(f"grounding mode must be one of {MODES}")
    id_map = load_id_map(id_map_path)
    if mcp_command:
        return MCPGrounding(mcp_command, mode, id_map=id_map, **tool_names)
    if bundle:
        return BundleGrounding(bundle, mode, id_map=id_map)
    raise ValueError("grounding needs --mcp-command or --mcp-bundle")
