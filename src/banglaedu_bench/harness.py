"""Evaluation harness: run a model over a split, score, and write predictions + summary."""

from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import __version__
from .adapters.base import Adapter
from .curriculum import BAND_ORDER, STREAM_ORDER, describe, exam_label
from .grounding import Grounding, NoGrounding
from .judge import JUDGE_PROMPT_VERSION, Judge
from .loader import item_hash, load_jsonl
from .normalize import normalize_text
from .prompts import PROMPT_VERSION, mcq_messages, short_messages, srijonshil_messages
from .protocol import protocol_card, same_model, threshold_block
from .scoring import Score, score_mcq, score_numeric, score_text


def _auto_text_key(key: dict) -> bool:
    """True if a text key is a short term (<= 3 words) that string matching can score."""
    refs = [key["text"], *key.get("aliases", [])]
    return any(0 < len(normalize_text(r).split()) <= 3 for r in refs)


def _score_written(
    text: str,
    question: str,
    key: dict,
    rubric: list[dict],
    marks: float,
    judge: Judge | None,
    exam: str = "",
) -> Score:
    """Numeric keys: auto-scored (full marks or 0). Text keys: judge if given, else match."""
    if "numeric" in key:
        return score_numeric(text, key, marks)
    if judge is None and not _auto_text_key(key):
        # Explanatory answer and no judge: not auto-scorable; excluded from the totals.
        return Score(0, marks, "needs_judge")
    if judge is not None:
        score, raw = judge.grade(question, key["text"], rubric, marks, text, exam=exam)
        if score is None:
            return Score(0, marks, "judge", detail=f"unparsed judge output: {raw[:200]}")
        return Score(score, marks, "judge", detail=raw[:300])
    return score_text(text, key, marks)


def eval_item(item: dict, model: Adapter, grounding: Grounding, judge: Judge | None = None) -> dict:
    """Evaluate one item; returns a prediction record."""
    rec: dict = {
        "id": item.get("id"),
        "task_type": item.get("task_type"),
        "topic_id": item.get("topic_id"),
        "chapter": (item.get("chapter") or {}).get("number"),
        "thinking_level": item.get("thinking_level"),
    }
    try:
        info = describe(item)
        exam = exam_label(info)
        rec.update(
            class_band=info["class_band"],
            subject=info["subject"],
            stream=info["stream"],
            class_level=info["class_level"],
        )
        ctx = grounding.context(item, item["question"]) if grounding.mode != "none" else ""
        meta = {"item": item, "grounding": ctx}
        rec["grounded"] = bool(ctx)
        if item["task_type"] == "mcq":
            out = model.generate(mcq_messages(item, ctx), meta=meta)
            sc = score_mcq(out, item)
            rec.update(output=out, **_flat(sc))
        elif item["task_type"] == "short_answer":
            out = model.generate(short_messages(item, ctx), meta=meta)
            sc = _score_written(
                out,
                item["question"],
                item["answer_key"],
                item["marking_rubric"],
                item["max_marks"],
                judge,
                exam,
            )
            rec.update(output=out, **_flat(sc))
        else:
            parts = []
            for part in item["parts"]:
                out = model.generate(
                    srijonshil_messages(item, part, ctx), meta={**meta, "part": part}
                )
                sc = _score_written(
                    out,
                    f"{item['question']}\n({part['label']}) {part['question']}",
                    part["answer_key"],
                    part["marking_rubric"],
                    part["marks"],
                    judge,
                    exam,
                )
                parts.append(
                    {
                        "label": part["label"],
                        "thinking_level": part["thinking_level"],
                        "output": out,
                        **_flat(sc),
                    }
                )
            rec["parts"] = parts
            scored = [p for p in parts if p["method"] != "needs_judge"]
            rec["score"] = sum(p["score"] for p in scored)
            rec["max_marks"] = sum(p["max_marks"] for p in scored)
            rec["n_parts_needing_judge"] = len(parts) - len(scored)
            rec["method"] = "parts"
    except Exception as exc:  # record failures instead of aborting the run
        rec.update(score=0, max_marks=item["max_marks"], method="error", detail=str(exc)[:300])
    return rec


def _flat(sc: Score) -> dict:
    d = sc.to_dict()
    return {k: v for k, v in d.items() if v is not None}


def summarize(preds: list[dict]) -> dict:
    """Marks-weighted scores overall and by task type, chapter, topic and thinking level."""

    def bucket():
        return {"score": 0.0, "max": 0.0, "n": 0}

    groups: dict[str, dict] = defaultdict(lambda: defaultdict(bucket))
    total = bucket()
    errors = unparsed = needs_judge = 0
    for p in preds:
        needs_judge += int(p.get("method") == "needs_judge")
        needs_judge += p.get("n_parts_needing_judge", 0)
        # A creative item whose every part still needs a judge has no marks to add.
        unscored_item = p.get("method") == "parts" and not p.get("max_marks")
        if p.get("method") == "error":
            errors += 1
        if p.get("method") in {"needs_judge", "error"} or unscored_item:
            continue
        for key, val in (
            ("task_type", p["task_type"]),
            ("chapter", f"ch{int(p['chapter']):02d}"),
            ("topic", p["topic_id"]),
            ("class_band", p.get("class_band") or "unknown"),
            ("subject", p.get("subject") or "unknown"),
            ("stream", p.get("stream") or "unknown"),
        ):
            g = groups[key][val]
            g["score"] += p["score"]
            g["max"] += p["max_marks"]
            g["n"] += 1
        # Thinking level: srijonshil parts count at their own levels.
        units = p.get("parts") or [p]
        for u in units:
            if u.get("method") == "needs_judge":
                continue
            g = groups["thinking_level"][u["thinking_level"]]
            g["score"] += u["score"]
            g["max"] += u["max_marks"]
            g["n"] += 1
            unparsed += u.get("method") == "unparsed"
        total["score"] += p["score"]
        total["max"] += p["max_marks"]
        total["n"] += 1

    for band in BAND_ORDER:
        groups["class_band"].setdefault(band, {"score": 0.0, "max": 0.0, "n": 0})

    def pct(b):
        return round(100 * b["score"] / b["max"], 2) if b["max"] else None

    def ordered(group: str, mapping: dict) -> list:
        if group == "class_band":
            first = [name for name in BAND_ORDER if name in mapping]
        elif group == "stream":
            first = [name for name in STREAM_ORDER if name in mapping]
        else:
            first = []
        rest = sorted(name for name in mapping if name not in first)
        return first + rest

    by = {
        k: {
            name: {"pct": pct(b), "n": b["n"], "score": b["score"], "max": b["max"]}
            for name in ordered(k, v)
            for b in [v[name]]
        }
        for k, v in groups.items()
    }
    task_pcts = [b["pct"] for b in by.get("task_type", {}).values() if b["pct"] is not None]
    return {
        "overall_pct_marks": pct(total),
        "macro_task_type_pct": round(sum(task_pcts) / len(task_pcts), 2) if task_pcts else None,
        "n_items": len(preds),
        "n_scored_items": total["n"],
        "n_errors": errors,
        "n_unparsed": unparsed,
        "n_units_needing_judge": needs_judge,
        "by": by,
    }


def run(
    data_path: str | Path,
    model: Adapter,
    out_dir: str | Path,
    *,
    grounding: Grounding | None = None,
    judge: Judge | None = None,
    split_name: str = "dev",
    workers: int = 4,
    limit: int | None = None,
    resume: bool = True,
) -> dict:
    if same_model(model, judge):
        raise ValueError(
            f"judge {judge.name!r} is the model under test. Use a different model to grade."
        )
    grounding = grounding or NoGrounding()
    items = load_jsonl(data_path)[:limit] if limit else load_jsonl(data_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pred_path = out_dir / "predictions.jsonl"

    done: dict[str, dict] = {}
    if resume and pred_path.exists():
        for line in pred_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("method") != "error":
                    done[r["id"]] = r
    todo = [it for it in items if it["id"] not in done]

    # MCP stdio clients are not thread-safe; serialise when grounding is live.
    n_workers = 1 if grounding.source == "mcp" else max(1, workers)
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        new = list(pool.map(lambda it: eval_item(it, model, grounding, judge), todo))
    by_id = {**done, **{r["id"]: r for r in new}}
    preds = [by_id[it["id"]] for it in items if it["id"] in by_id]
    with pred_path.open("w", encoding="utf-8") as fh:
        for r in preds:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "benchmark": "banglaedu-bench",
        "harness_version": __version__,
        "prompt_version": PROMPT_VERSION,
        "judge": judge.name if judge else None,
        "judge_prompt_version": JUDGE_PROMPT_VERSION if judge else None,
        "model": model.name,
        "split": split_name,
        "grounding_mode": grounding.mode,
        "grounding_source": grounding.source,
        "data_sha256_of_item_hashes": _data_fingerprint(items),
        "item_version": sorted({it.get("version", "?") for it in items}),
        "n_verified_items": sum(1 for it in items if it.get("verified") is True),
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        **summarize(preds),
    }
    summary["protocol"] = protocol_card(model, judge)
    summary["threshold"] = threshold_block(
        items, preds, model, summary.get("by", {}).get("class_band", {})
    )
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def _data_fingerprint(items: list[dict]) -> str:
    import hashlib

    h = hashlib.sha256()
    for it in items:
        h.update(item_hash(it).encode())
    return h.hexdigest()
