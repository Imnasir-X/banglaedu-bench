"""Record topic ids that nctb-data 0.1.0 cannot align.

nctb-data 0.1.0 publishes structure for physics class 9–10 only. College,
primary, and junior ids stay provisional. This script does not invent a
shared id.

Run from the repo root: uv run python scripts/record_topic_gap.py
"""

from __future__ import annotations

import csv
import json
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

OUT = ROOT / "data" / "topic_gap.csv"
NOTE = (
    "nctb-data 0.1.0 (edition 2026, draft) publishes physics class 9-10 only "
    "(nctb:phy:c9-10:bn and nctb:phy:c9-10:en). No shared id exists for this item. "
    "topic_id_status stays provisional."
)
COLUMNS = [
    "item_id",
    "split",
    "subject",
    "class_level",
    "provisional_topic_id",
    "shared_topic_id",
    "status",
    "note",
]


def gap_rows(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        for item in load_jsonl(path):
            rows.append(
                {
                    "item_id": item["id"],
                    "split": item["split"],
                    "subject": item["subject"],
                    "class_level": json.dumps(item["class_level"]),
                    "provisional_topic_id": item["topic_id"],
                    "shared_topic_id": "",
                    "status": "no_nctb_data_bundle",
                    "note": NOTE,
                }
            )
    return rows


def write_gap(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = gap_rows([COLLEGE_PATH, PRIMARY_PATH, JUNIOR_PATH])
    write_gap(rows, OUT)
    filled = sum(1 for row in rows if row["shared_topic_id"])
    print(f"wrote {len(rows)} rows to {OUT}; shared ids filled: {filled}")


if __name__ == "__main__":
    main()
