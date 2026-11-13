"""Export review sheets and an author recheck. Reviewer 2 stays blank.

The author recheck is not a second teacher. review-apply will not set
verified=true from these files.

Run from the repo root: uv run python scripts/write_author_recheck.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banglaedu_bench.loader import (  # noqa: E402
    COLLEGE_PATH,
    JUNIOR_PATH,
    PRIMARY_PATH,
    load_jsonl,
)
from banglaedu_bench.review import export_sheet, read_sheet, sheet_columns  # noqa: E402

NAME = "author-recheck"
BASE_NOTE = (
    "Author recheck on 2026-11-13, not an independent teacher. "
    "Stored numeric expressions were recomputed. "
    "The topic id is provisional because nctb-data 0.1.0 has no book for this class. "
    "syllabus_ok is no until a teacher opens the 2026 book. "
    "Reviewer 2 has not scored this row."
)
# Question text -> (answer_correct, rubric_ok, extra note).
FLAGS = {
    "She ___ a student.": (
        "no",
        "no",
        " The key accepts only 'is'. 'was' is also grammatical, so the key is incomplete.",
    ),
    "অতিক্রান্ত দূরত্ব নির্ণয় কর": (
        "yes",
        "no",
        " Part ঘ's numeric key scores 25 m and does not score the 'half of vt' clause.",
    ),
    "একই সময়ে ২০০ মিটার হাঁটলে": (
        "yes",
        "no",
        " Part ঘ's numeric key scores 4 m/s and does not score the 'how many times' clause.",
    ),
}

PAIRS = (
    (
        "college",
        COLLEGE_PATH,
        ROOT / "review" / "review_sheet_college.csv",
        ROOT / "review" / "college_r1.csv",
    ),
    (
        "primary",
        PRIMARY_PATH,
        ROOT / "review" / "review_sheet_primary.csv",
        ROOT / "review" / "primary_r1.csv",
    ),
    (
        "junior",
        JUNIOR_PATH,
        ROOT / "review" / "review_sheet_junior.csv",
        ROOT / "review" / "junior_r1.csv",
    ),
)


def fill(items: list[dict], blank: Path, out: Path) -> int:
    export_sheet(items, blank)
    export_sheet(items, out)
    rows = read_sheet(out)
    for row in rows:
        answer, rubric, extra = "yes", "yes", ""
        for needle, flag in FLAGS.items():
            if needle in row["question"]:
                answer, rubric, extra = flag
                break
        row["r1_name"] = NAME
        row["r1_answer_correct"] = answer
        row["r1_bangla_ok"] = "yes"
        row["r1_syllabus_ok"] = "no"
        row["r1_rubric_ok"] = rubric
        row["r1_verdict"] = "revise"
        row["r1_notes"] = BASE_NOTE + extra
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=sheet_columns())
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    for name, path, blank, filled in PAIRS:
        n = fill(load_jsonl(path), blank, filled)
        print(f"wrote {n} {name} rows to {blank.name} and {filled.name}")


if __name__ == "__main__":
    main()
