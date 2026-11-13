"""Fill reviewer 1 on the public physics dev sheet.

Reviewer 2 stays empty. review-apply will not set verified=true from this file.
The notes are a technical audit, not a second teacher.

Run: uv run python scripts/write_physics_r1.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banglaedu_bench.loader import DEV_PATH, load_jsonl  # noqa: E402
from banglaedu_bench.review import export_sheet, read_sheet, sheet_columns  # noqa: E402

OUT = ROOT / "review" / "physics_dev_r1.csv"
NAME = "technical-audit"
SECTION_NOTE = (
    "Answer key checked on 2026-11-13. "
    "The section id inside topic_id was not opened against the 2026 NCTB book, "
    "so syllabus_ok is no and the verdict is revise until a teacher confirms the section."
)
EXTRA = {
    "bebench-phy-004": " Significant figures: 0.00450 has three (4, 5, and the trailing zero). Confirm section 1.7 of the 2026 book.",
    "bebench-phy-013": " School ordering is rolling < sliding < static. Confirm that wording in the book.",
    "bebench-phy-022": " Key uses the school value 4200 J kg^-1 K^-1. Confirm the figure printed in the 2026 book.",
    "bebench-phy-054": " Latent heat of fusion used is 336000 J kg^-1. Confirm the book's value.",
    "bebench-phy-063": " Arithmetic is 5 g after four half-lives. Confirm that অর্ধায়ু is in the shortened 2026 chapter 13.",
    "bebench-phy-069": " i = r is the usual second law of reflection. Confirm the book numbers it second.",
    "bebench-phy-070": (
        " Part ক defines acceleration only as an increase in speed. "
        "The definition should be the rate of change of velocity, including a decrease and a change of direction. "
        "Parts খ, গ and ঘ check out, including the 550 m total."
    ),
    "bebench-phy-076": " Image distance 60 cm and |m| = 2, and the key also accepts -2. Confirm the book's sign convention.",
}


def main() -> None:
    items = load_jsonl(DEV_PATH)
    export_sheet(items, OUT)
    rows = read_sheet(OUT)
    for row in rows:
        iid = row["id"]
        row["r1_name"] = NAME
        row["r1_answer_correct"] = "no" if iid == "bebench-phy-070" else "yes"
        row["r1_bangla_ok"] = "yes"
        row["r1_syllabus_ok"] = "no"
        row["r1_rubric_ok"] = "no" if iid == "bebench-phy-070" else "yes"
        row["r1_verdict"] = "revise"
        row["r1_notes"] = SECTION_NOTE + EXTRA.get(iid, "")
    with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=sheet_columns())
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
