"""Leaderboard: collect run summaries, pair with/without-MCP runs, emit Markdown + CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def collect(results_dir: str | Path) -> list[dict]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(Path(results_dir).glob("**/summary.json"))
    ]


def _pct(s: dict, group: str, key: str):
    return s.get("by", {}).get(group, {}).get(key, {}).get("pct")


def _fmt(v) -> str:
    return "—" if v is None else f"{v:.1f}"


def build_rows(summaries: list[dict], split: str) -> list[dict]:
    """One row per (model, judge); 'none' grounding vs best MCP mode side by side."""
    runs: dict[tuple, dict] = {}
    for s in summaries:
        if s.get("split") != split:
            continue
        key = (s["model"], s.get("judge"))
        runs.setdefault(key, {})[s.get("grounding_mode", "none")] = s
    rows = []
    for (model, judge), modes in runs.items():
        base = modes.get("none")
        mcp = modes.get("search")
        topic = modes.get("topic")
        ref = base or mcp or topic
        row = {
            "model": model,
            "judge": judge or "none (exact/numeric only)",
            "n_items": ref["n_items"],
            "overall_no_mcp": base["overall_pct_marks"] if base else None,
            "overall_mcp_search": mcp["overall_pct_marks"] if mcp else None,
            "delta_mcp_search": (
                round(mcp["overall_pct_marks"] - base["overall_pct_marks"], 2)
                if base and mcp
                else None
            ),
            "overall_mcp_topic": topic["overall_pct_marks"] if topic else None,
            "mcq": _pct(ref, "task_type", "mcq"),
            "short_answer": _pct(ref, "task_type", "short_answer"),
            "srijonshil": _pct(ref, "task_type", "srijonshil"),
            "chapters": {k: v["pct"] for k, v in ref.get("by", {}).get("chapter", {}).items()},
            "bands": {k: v["pct"] for k, v in ref.get("by", {}).get("class_band", {}).items()},
            "prompt_version": ref.get("prompt_version"),
            "n_verified_items": ref.get("n_verified_items"),
            "comparable": (ref.get("threshold") or {}).get("comparable"),
        }
        rows.append(row)
    rows.sort(key=lambda r: -(r["overall_no_mcp"] or r["overall_mcp_search"] or 0))
    return rows


def to_markdown(rows: list[dict], split: str) -> str:
    out = [
        f"## BanglaEdu Bench — {split} split",
        "",
        "Scores are % of available marks. Read them by class band: primary (5), junior (6–8),",
        "SSC (9–10) and college HSC (11–12). One average is not a pass. MCQ is exact match;",
        "numeric answers use tolerance; written answers use the named judge.",
        "Δ = with MCP (search grounding) minus without.",
        "",
        "| # | Model | Judge | Items | No MCP | MCP (search) | Δ | MCP (topic, upper bound) "
        "| MCQ | Short | Srijonshil |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        d = r["delta_mcp_search"]
        out.append(
            f"| {i} | {r['model']} | {r['judge']} | {r['n_items']} | {_fmt(r['overall_no_mcp'])} "
            f"| {_fmt(r['overall_mcp_search'])} | {'—' if d is None else f'{d:+.1f}'} "
            f"| {_fmt(r['overall_mcp_topic'])} | {_fmt(r['mcq'])} | {_fmt(r['short_answer'])} "
            f"| {_fmt(r['srijonshil'])} |"
        )
    bands = [b for b in ("primary", "junior", "ssc", "hsc") if any(b in r["bands"] for r in rows)]
    if bands:
        out += ["", "### By class band (no-MCP run where available)", ""]
        out.append("| Model | " + " | ".join(bands) + " |")
        out.append("|---|" + "---|" * len(bands))
        for r in rows:
            out.append(
                "| "
                + r["model"]
                + " | "
                + " | ".join(_fmt(r["bands"].get(b)) for b in bands)
                + " |"
            )
    chapters = sorted({c for r in rows for c in r["chapters"]})
    if chapters:
        out += ["", "### Per-chapter breakdown (no-MCP run where available)", ""]
        out.append("| Model | " + " | ".join(chapters) + " |")
        out.append("|---|" + "---|" * len(chapters))
        for r in rows:
            out.append(
                f"| {r['model']} | "
                + " | ".join(_fmt(r["chapters"].get(c)) for c in chapters)
                + " |"
            )
    if rows and not any(r["n_verified_items"] for r in rows):
        out += [
            "",
            "> Warning: no item in this split has passed two-reviewer verification yet "
            "(verified=false). Treat these numbers as a harness demo, not as results.",
        ]
    return "\n".join(out) + "\n"


def write(rows: list[dict], split: str, out_dir: str | Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"leaderboard_{split}.md"
    md.write_text(to_markdown(rows, split), encoding="utf-8")
    cs = out_dir / f"leaderboard_{split}.csv"
    cols = [k for k in (rows[0] if rows else {}) if k not in {"chapters", "bands"}]
    with cs.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in cols})
    return md, cs
