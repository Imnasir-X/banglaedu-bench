"""Two-reviewer workflow: export a sheet, compute agreement, apply verdicts back to items.

The sheet is plain UTF-8 CSV with a BOM so Excel and Google Sheets open Bangla
correctly. Each reviewer fills only their own columns, independently.

Reviewer columns (rN = r1 / r2):
  rN_name            reviewer name or initials
  rN_answer_correct  yes | no            is the answer key correct?
  rN_bangla_ok       yes | no            is the Bangla clear and correct?
  rN_syllabus_ok     yes | no            within the NCTB Class 9-10 syllabus, topic id right?
  rN_rubric_ok       yes | no            is the marking rubric fair and complete?
  rN_verdict         accept | revise | reject
  rN_notes           free text (corrections go here)
Adjudication (only when reviewers disagree): adjudicator, final_verdict, final_notes.

An item becomes verified=true only when both verdicts are accept with
answer_correct=yes from both, or an adjudicator sets final_verdict=accept.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .agreement import cohens_kappa, interpret_kappa, percent_agreement

ITEM_COLS = [
    "id", "version", "split", "task_type", "topic_id", "chapter", "thinking_level",
    "difficulty", "question", "options", "answer_key", "marking_rubric", "explanation",
    "answer_check",
]  # fmt: skip
REVIEWER_FIELDS = [
    "name", "answer_correct", "bangla_ok", "syllabus_ok", "rubric_ok", "verdict", "notes",
]  # fmt: skip
ADJ_COLS = ["adjudicator", "final_verdict", "final_notes"]
VERDICTS = ["accept", "revise", "reject"]
YESNO = ["yes", "no"]


def _j(v) -> str:
    return json.dumps(v, ensure_ascii=False) if v is not None else ""


def _item_row(it: dict) -> dict:
    if it["task_type"] == "srijonshil":
        key = {p["label"]: p["answer_key"] for p in it["parts"]}
        rubric = {p["label"]: p["marking_rubric"] for p in it["parts"]}
        q = (
            it["question"]
            + "\n"
            + "\n".join(f"({p['label']}) {p['question']}" for p in it["parts"])
        )
        check = {p["label"]: p.get("answer_check") for p in it["parts"]}
    else:
        key, rubric, q, check = (
            it["answer_key"],
            it["marking_rubric"],
            it["question"],
            it.get("answer_check"),
        )
    return {
        "id": it["id"],
        "version": it["version"],
        "split": it["split"],
        "task_type": it["task_type"],
        "topic_id": it["topic_id"],
        "chapter": f"{it['chapter']['number']}: {it['chapter']['title_bn']}",
        "thinking_level": it["thinking_level"],
        "difficulty": it["difficulty"],
        "question": q,
        "options": " | ".join(f"({o['label']}) {o['text']}" for o in it.get("options", [])),
        "answer_key": _j(key),
        "marking_rubric": _j(rubric),
        "explanation": it["explanation"],
        "answer_check": _j(check),
    }


def sheet_columns() -> list[str]:
    rev = [f"r{n}_{f}" for n in (1, 2) for f in REVIEWER_FIELDS]
    return ITEM_COLS + rev + ADJ_COLS


def export_sheet(items: list[dict], path: str | Path) -> int:
    cols = sheet_columns()
    with Path(path).open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for it in items:
            w.writerow({**dict.fromkeys(cols, ""), **_item_row(it)})
    return len(items)


def read_sheet(path: str | Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _clean(v: str) -> str:
    return (v or "").strip().lower()


def agreement_report(rows: list[dict]) -> dict:
    """Agreement between r1 and r2 on every reviewer field both filled in."""
    report: dict = {"n_rows": len(rows), "fields": {}}
    for field, labels in (
        ("verdict", VERDICTS),
        ("answer_correct", YESNO),
        ("bangla_ok", YESNO),
        ("syllabus_ok", YESNO),
        ("rubric_ok", YESNO),
    ):
        pairs = [
            (_clean(r[f"r1_{field}"]), _clean(r[f"r2_{field}"]))
            for r in rows
            if _clean(r.get(f"r1_{field}")) in labels and _clean(r.get(f"r2_{field}")) in labels
        ]
        if not pairs:
            report["fields"][field] = {"n": 0}
            continue
        a, b = [p[0] for p in pairs], [p[1] for p in pairs]
        k = cohens_kappa(a, b, labels=labels)
        report["fields"][field] = {
            "n": len(pairs),
            "percent_agreement": round(100 * percent_agreement(a, b), 1),
            "cohens_kappa": round(k, 3),
            "kappa_band": interpret_kappa(k),
        }
    report["n_both_accept"] = sum(
        1
        for r in rows
        if _clean(r.get("r1_verdict")) == "accept" and _clean(r.get("r2_verdict")) == "accept"
    )
    report["n_needing_adjudication"] = sum(
        1
        for r in rows
        if _clean(r.get("r1_verdict")) in VERDICTS
        and _clean(r.get("r2_verdict")) in VERDICTS
        and _clean(r["r1_verdict"]) != _clean(r["r2_verdict"])
        and not _clean(r.get("final_verdict"))
    )
    return report


def final_verdict(row: dict) -> str | None:
    fv = _clean(row.get("final_verdict"))
    if fv in VERDICTS:
        return fv
    v1, v2 = _clean(row.get("r1_verdict")), _clean(row.get("r2_verdict"))
    ok = (
        _clean(row.get("r1_answer_correct")) == "yes"
        and _clean(row.get("r2_answer_correct")) == "yes"
    )
    if v1 == v2 == "accept" and ok:
        return "accept"
    if v1 == v2 and v1 in ("revise", "reject"):
        return v1
    return None  # disagreement or incomplete: needs adjudication


def apply_reviews(items: list[dict], rows: list[dict]) -> tuple[list[dict], dict]:
    """Return updated items (verified flag + review record) and counts."""
    by_id = {r["id"]: r for r in rows}
    counts = {"accept": 0, "revise": 0, "reject": 0, "pending": 0}
    out = []
    for it in items:
        it = json.loads(json.dumps(it))  # deep copy
        row = by_id.get(it["id"])
        verdict = final_verdict(row) if row else None
        if row:
            it["review"] = {
                "reviewers": [
                    {f: row.get(f"r{n}_{f}", "") for f in REVIEWER_FIELDS}
                    for n in (1, 2)
                    if row.get(f"r{n}_name")
                ],
                "adjudicator": row.get("adjudicator", ""),
                "final_verdict": verdict or "pending",
            }
        it["verified"] = verdict == "accept" and len(it.get("review", {}).get("reviewers", [])) >= 2
        counts[verdict or "pending"] += 1
        out.append(it)
    return out, counts
