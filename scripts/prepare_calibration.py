"""Build a pending judge-calibration sheet from public items only.

Two or three offline mocks stand in when no local model server is up. Their
replies are not a teacher score. human_score stays empty, and the judge is
not accepted. The private test split is not read.

Run from the repo root: uv run python scripts/prepare_calibration.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banglaedu_bench.adapters import make_adapter  # noqa: E402
from banglaedu_bench.baselines import port_open  # noqa: E402
from banglaedu_bench.calibration import make_sheet, read_sheet, run_calibration  # noqa: E402
from banglaedu_bench.harness import run  # noqa: E402
from banglaedu_bench.judge import Judge  # noqa: E402
from banglaedu_bench.loader import COLLEGE_PATH, DEV_PATH, JUNIOR_PATH, PRIMARY_PATH  # noqa: E402

SHEET = ROOT / "review" / "judge_calibration_pending.csv"
STATUS = ROOT / "review" / "judge_calibration_status.json"
MOCKS = ("mock-random", "mock-constant", "mock-grounded")
PUBLIC = (
    ("dev", DEV_PATH),
    ("college", COLLEGE_PATH),
    ("primary", PRIMARY_PATH),
    ("junior", JUNIOR_PATH),
)


def main() -> int:
    real_local = port_open("127.0.0.1", 11434) or port_open("127.0.0.1", 8000)
    splits = list(PUBLIC[:2])
    with tempfile.TemporaryDirectory() as tmp:
        n, used = _sample(Path(tmp), splits)
        if n < 50:
            n, used = _sample(Path(tmp), list(PUBLIC))
    rows = read_sheet(SHEET)
    if len(rows) < 50:
        raise SystemExit(f"public written answers produced {len(rows)} rows; need 50")
    if any(str(row.get("human_score", "")).strip() for row in rows):
        raise SystemExit("human_score must stay empty until a teacher scores the sheet")
    decision = run_calibration(SHEET, Judge(make_adapter("mock-judge")))
    status = {
        "accepted": decision["decision"]["accepted"],
        "reasons": decision["decision"]["reasons"],
        "real_local_models": real_local,
        "models": list(MOCKS),
        "model_note": (
            "Offline mocks, because no local model server was used for these replies. "
            "mock-grounded had no MCP bundle, so its written answers match mock-constant. "
            "A teacher still has to score human_score blind."
        ),
        "splits": used,
        "private_split_used": False,
        "third_party_api": False,
        "n_rows": len(rows),
        "human_score_filled": 0,
        "n_compared": decision.get("n", 0),
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} rows to {SHEET}")
    print("judge not accepted")
    return 2


def _sample(tmp: Path, splits: list[tuple[str, Path]]) -> tuple[int, list[str]]:
    pred_paths = []
    for spec in MOCKS:
        adapter = make_adapter(spec)
        for name, path in splits:
            out = tmp / f"{name}__{spec}"
            run(path, adapter, out, split_name=name)
            pred_paths.append(out / "predictions.jsonl")
    n = make_sheet([path for _, path in splits], pred_paths, SHEET, n=50, seed=13)
    return n, [name for name, _ in splits]


if __name__ == "__main__":
    raise SystemExit(main())
