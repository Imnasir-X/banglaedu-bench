"""Load and filter BanglaEdu Bench JSONL files."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEV_PATH = PROJECT_ROOT / "data" / "dev" / "dev.jsonl"
# The test split is private: gitignored, never published, never sent to
# third-party APIs by maintainers except for scored evaluation runs.
TEST_PATH = PROJECT_ROOT / "data" / "private" / "test.jsonl"
SPLIT_PATHS = {"dev": DEV_PATH, "test": TEST_PATH}


class DataError(ValueError):
    pass


def load_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        raise DataError(f"{path} not found")
    items: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise DataError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return items


def resolve_split(split_or_path: str | Path) -> Path:
    s = str(split_or_path)
    return SPLIT_PATHS[s] if s in SPLIT_PATHS else Path(s)


def load_items(
    split_or_path: str | Path = "dev",
    *,
    task_types: Iterable[str] | None = None,
    chapters: Iterable[int] | None = None,
    verified_only: bool = False,
    limit: int | None = None,
) -> list[dict]:
    """Load items from a split name ('dev'/'test') or a JSONL path, with filters."""
    items = load_jsonl(resolve_split(split_or_path))
    tts = set(task_types) if task_types else None
    chs = set(chapters) if chapters else None
    out = [
        it
        for it in items
        if (tts is None or it.get("task_type") in tts)
        and (chs is None or it.get("chapter", {}).get("number") in chs)
        and (not verified_only or it.get("verified") is True)
    ]
    return out[:limit] if limit else out


def item_hash(item: dict) -> str:
    """SHA-256 of an item's canonical JSON.

    Publishing these for the private test split commits to its content without
    revealing it; a later reveal can be checked against the commitment.
    """
    canonical = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
