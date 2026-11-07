"""LLM-judge calibration against human-scored answers.

1. `make_sheet`: sample written-answer units (short answers with text keys and
   srijonshil parts without a numeric key) from one or more prediction files into
   a CSV. Teachers fill `human_score` (and `human_grader`) blind to the judge.
2. `run_calibration`: score the same answers with the judge and report agreement:
   exact agreement, within-1-mark agreement, mean absolute error, quadratic
   weighted kappa per mark scale, and pass/fail kappa (score >= half marks).
The target in the spec is 50 human-scored answers; publish the report with results.
"""

from __future__ import annotations

import csv
import io
import json
import random
from collections import defaultdict
from pathlib import Path

from .agreement import cohens_kappa, interpret_kappa, percent_agreement
from .judge import Judge
from .loader import load_jsonl

SHEET_COLS = [
    "unit_id", "item_id", "part", "model", "question", "reference_answer", "marking_rubric",
    "max_marks", "model_answer", "human_score", "human_grader", "judge_score", "judge_raw",
]  # fmt: skip


def written_units(items: list[dict], preds: list[dict], model: str) -> list[dict]:
    by_id = {it["id"]: it for it in items}
    units = []
    for p in preds:
        it = by_id.get(p["id"])
        if not it:
            continue
        if it["task_type"] == "short_answer" and "numeric" not in it["answer_key"]:
            units.append(_unit(it, None, p.get("output", ""), model))
        elif it["task_type"] == "srijonshil":
            outs = {x["label"]: x.get("output", "") for x in p.get("parts", [])}
            for part in it["parts"]:
                if "numeric" not in part["answer_key"]:
                    units.append(_unit(it, part, outs.get(part["label"], ""), model))
    return units


def _unit(it: dict, part: dict | None, answer: str, model: str) -> dict:
    src = part or it
    q = (
        it["question"]
        if part is None
        else f"{it['question']}\n({part['label']}) {part['question']}"
    )
    label = part["label"] if part else ""
    return {
        "unit_id": f"{it['id']}{'.' + label if label else ''}::{model}",
        "item_id": it["id"],
        "part": label,
        "model": model,
        "question": q,
        "reference_answer": src["answer_key"]["text"],
        "marking_rubric": json.dumps(src["marking_rubric"], ensure_ascii=False),
        "max_marks": src["marks"] if part else it["max_marks"],
        "model_answer": answer,
    }


def make_sheet(
    items_path: str | Path,
    pred_paths: list[str | Path],
    out: str | Path,
    n: int = 50,
    seed: int = 13,
) -> int:
    items = load_jsonl(items_path)
    units: list[dict] = []
    for pp in pred_paths:
        summary = Path(pp).with_name("summary.json")
        model = (
            json.loads(summary.read_text())["model"] if summary.exists() else Path(pp).parent.name
        )
        units += written_units(items, load_jsonl(pp), model)
    random.Random(seed).shuffle(units)
    units = units[:n]
    with Path(out).open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SHEET_COLS)
        w.writeheader()
        for u in units:
            w.writerow({**dict.fromkeys(SHEET_COLS, ""), **u})
    return len(units)


def read_sheet(path: str | Path) -> list[dict]:
    return list(csv.DictReader(io.StringIO(Path(path).read_text(encoding="utf-8-sig"))))


def agreement_stats(human: list[float], judge: list[float], max_marks: list[float]) -> dict:
    n = len(human)
    if n == 0:
        return {"n": 0}
    exact = sum(round(h) == round(j) for h, j in zip(human, judge, strict=False)) / n
    within1 = sum(abs(h - j) <= 1 for h, j in zip(human, judge, strict=False)) / n
    mae = sum(abs(h - j) for h, j in zip(human, judge, strict=False)) / n
    passes_h = ["pass" if h >= m / 2 else "fail" for h, m in zip(human, max_marks, strict=False)]
    passes_j = ["pass" if j >= m / 2 else "fail" for j, m in zip(judge, max_marks, strict=False)]
    pf_kappa = cohens_kappa(passes_h, passes_j, labels=["fail", "pass"])
    per_scale = {}
    groups: dict[float, list[tuple[int, int]]] = defaultdict(list)
    for h, j, m in zip(human, judge, max_marks, strict=False):
        groups[m].append((round(h), round(j)))
    for m, pairs in sorted(groups.items()):
        labels = list(range(int(m) + 1))
        a, b = [p[0] for p in pairs], [p[1] for p in pairs]
        qwk = cohens_kappa(a, b, labels=labels, weights="quadratic")
        per_scale[f"max_{int(m)}"] = {
            "n": len(pairs),
            "exact_pct": round(100 * percent_agreement(a, b), 1),
            "quadratic_weighted_kappa": round(qwk, 3),
        }
    return {
        "n": n,
        "exact_agreement_pct": round(100 * exact, 1),
        "within_1_mark_pct": round(100 * within1, 1),
        "mean_abs_error_marks": round(mae, 3),
        "pass_fail_kappa": round(pf_kappa, 3),
        "pass_fail_kappa_band": interpret_kappa(pf_kappa),
        "per_mark_scale": per_scale,
    }


def run_calibration(sheet: str | Path, judge: Judge, out_csv: str | Path | None = None) -> dict:
    rows = read_sheet(sheet)
    human, jud, mx = [], [], []
    for r in rows:
        if not str(r.get("human_score", "")).strip():
            continue
        m = float(r["max_marks"])
        score, raw = judge.grade(
            r["question"],
            r["reference_answer"],
            json.loads(r["marking_rubric"]),
            m,
            r["model_answer"],
        )
        r["judge_score"] = "" if score is None else score
        r["judge_raw"] = raw[:500]
        if score is None:
            continue
        human.append(float(r["human_score"]))
        jud.append(score)
        mx.append(m)
    report = {
        "judge": judge.name,
        "n_rows": len(rows),
        "n_human_scored": sum(1 for r in rows if str(r.get("human_score", "")).strip()),
        **agreement_stats(human, jud, mx),
    }
    if out_csv:
        with Path(out_csv).open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=SHEET_COLS)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in SHEET_COLS})
    return report
