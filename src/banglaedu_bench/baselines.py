"""Local baselines on the private test split.

A published baseline is five to eight local models, temperature 0, 1024 tokens,
with and without MCP, scored on data/private/test.jsonl. That file stays off
third-party APIs. Mock adapters are not a baseline. The public report always
lists primary, junior, SSC, and college as separate columns.
"""

from __future__ import annotations

import json
import socket
from collections.abc import Callable
from pathlib import Path

from .loader import TEST_PATH
from .protocol import MAX_TOKENS, TEMPERATURE, left_the_machine

REMOTE_PROVIDERS = {"openrouter", "openai", "groq"}
LOCAL_PROVIDERS = {"ollama", "vllm"}
BANDS = ("primary", "junior", "ssc", "hsc")
BAND_LABEL = {
    "primary": "primary (class 5)",
    "junior": "junior (class 6–8)",
    "ssc": "SSC (class 9–10)",
    "hsc": "college (class 11–12)",
}


def refusal(spec: str, base_url: str | None = None) -> str | None:
    """Why this adapter must not score the private test. None means it may."""
    if spec.startswith("mock-"):
        return "mock adapters are not a baseline"
    if ":" not in spec:
        return f"unknown adapter {spec}"
    provider, _model = spec.split(":", 1)
    if provider in REMOTE_PROVIDERS:
        return "the private test stays off third-party APIs"
    if provider == "openai-compat":
        if not base_url:
            return "openai-compat needs a base URL on this machine"
        if _remote(base_url):
            return "base URL is not on this machine"
        return None
    if provider in LOCAL_PROVIDERS:
        if base_url and _remote(base_url):
            return "base URL is not on this machine"
        return None
    return f"unknown provider {provider}"


def _remote(base_url: str) -> bool:
    class _Host:
        def __init__(self, url: str) -> None:
            self.base_url = url

    return left_the_machine(_Host(base_url))


def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def commitment_counts(path: Path) -> dict[str, int]:
    """How many committed private ids fall in each band. Ids only, no item text."""
    counts = dict.fromkeys(BANDS, 0)
    if not path.exists():
        return counts
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("bebench-"):
            continue
        item_id = line.split()[0]
        if "-c5-" in item_id:
            counts["primary"] += 1
        elif "-c6-8-" in item_id:
            counts["junior"] += 1
        elif "-c11-12-" in item_id:
            counts["hsc"] += 1
        else:
            # Schema 0.1 physics ids (bebench-phy-NNN) are class 9–10.
            counts["ssc"] += 1
    return counts


def probe(
    *,
    private_path: Path = TEST_PATH,
    commitments: Path | None = None,
    models: list[str] | None = None,
    bundle: Path | None = None,
    port_open_fn: Callable[[str, int], bool] | None = None,
) -> dict:
    """Whether a real local baseline can start. Does not call a model."""
    check = port_open_fn or port_open
    specs = list(models or [])
    refusals = [message for spec in specs if (message := refusal(spec))]
    ollama = check("127.0.0.1", 11434)
    vllm = check("127.0.0.1", 8000)
    present = private_path.exists()
    counts = commitment_counts(commitments) if commitments else dict.fromkeys(BANDS, 0)
    ready = present and (ollama or vllm) and 5 <= len(specs) <= 8 and not refusals
    blocked = []
    if not present:
        blocked.append("private test file is not on this machine")
    if not (ollama or vllm):
        blocked.append("no local server on 127.0.0.1:11434 or 127.0.0.1:8000")
    if not specs:
        blocked.append("no local models are configured")
    elif not (5 <= len(specs) <= 8):
        blocked.append("a baseline uses five to eight models")
    blocked.extend(refusals)
    return {
        "ran": False,
        "ready": ready,
        "private_test_present": present,
        "local_server": ollama or vllm,
        "ollama_11434": ollama,
        "vllm_8000": vllm,
        "mcp_bundle": str(bundle) if bundle else None,
        "third_party_api": False,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "judge": None,
        "judge_note": "The judge is not accepted, so written answers stay out of the percent.",
        "models": specs,
        "blocked": blocked,
        "private_items_by_band": counts,
        "bands": list(BANDS),
    }


def public_report(status: dict, scores: dict | None = None) -> str:
    """Markdown table with primary, junior, SSC, and college in separate columns.

    `scores` maps (model, mcp_label) to {band: percent or None}. An empty score
    map means the run did not happen.
    """
    lines = [
        "# BanglaEdu Bench public baseline report",
        "",
        "Temperature 0, 1024 tokens. The private test split is not sent to a",
        "third-party API. Primary, junior, SSC, and college are separate columns.",
        "A cell is a percent of marks scored in that band. `not run` means no",
        "local baseline was executed. `no private items` means the committed",
        "private split has no items of that band, so there is nothing to score.",
        "",
    ]
    if status.get("ran"):
        lines.append("This file records a local run on the private test split.")
    else:
        lines.append("This file does not record a model score. The run did not start.")
        lines.append("")
        for reason in status.get("blocked") or []:
            lines.append(f"- {reason}")
    lines.extend(
        ["", "| Model | MCP | primary | junior | SSC | college |", "|---|---|---|---|---|---|"]
    )
    counts = status.get("private_items_by_band") or {}
    if not scores:
        cells = []
        for band in BANDS:
            n = counts.get(band, 0)
            cells.append("no private items" if n == 0 else "not run")
        lines.append("| — | — | " + " | ".join(cells) + " |")
    else:
        for (model, mcp), band_pct in scores.items():
            shown = []
            for band in BANDS:
                value = band_pct.get(band)
                if counts.get(band, 0) == 0 and value is None:
                    shown.append("no private items")
                elif value is None:
                    shown.append("—")
                else:
                    shown.append(f"{value:.1f}")
            lines.append(f"| {model} | {mcp} | " + " | ".join(shown) + " |")
    lines.extend(
        [
            "",
            "The judge column is absent because a teacher has not accepted a judge.",
            "Written answers that need a judge are left out of any percent above.",
            "",
        ]
    )
    return "\n".join(lines)


def write_blocked(status: dict, report_path: Path, status_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(public_report(status), encoding="utf-8")
    status_path.write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
