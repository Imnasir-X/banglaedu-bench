import csv

import pytest

from banglaedu_bench.adapters import make_adapter
from banglaedu_bench.agreement import cohens_kappa, percent_agreement
from banglaedu_bench.calibration import SHEET_COLS, agreement_stats, make_sheet, run_calibration
from banglaedu_bench.harness import run
from banglaedu_bench.judge import Judge, parse_judge_score
from banglaedu_bench.loader import DEV_PATH, load_jsonl
from banglaedu_bench.review import (
    agreement_report,
    apply_reviews,
    export_sheet,
    final_verdict,
    read_sheet,
    sheet_columns,
)
from banglaedu_bench.schema import validate_items


def test_kappa_known_values():
    a = ["yes", "yes", "no", "no", "yes", "no"]
    assert cohens_kappa(a, a) == pytest.approx(1.0)
    b = ["no", "no", "yes", "yes", "no", "yes"]
    assert cohens_kappa(a, b) == pytest.approx(-1.0)
    # Classic 2x2 example: po = 0.7, pe = 0.5 -> kappa 0.4
    x = ["y"] * 50 + ["n"] * 50
    y = ["y"] * 35 + ["n"] * 15 + ["y"] * 15 + ["n"] * 35
    assert percent_agreement(x, y) == pytest.approx(0.7)
    assert cohens_kappa(x, y) == pytest.approx(0.4)


def test_weighted_kappa_penalises_far_disagreement_more():
    a = [0, 1, 2, 3, 4]
    near = [1, 1, 2, 3, 4]
    far = [4, 1, 2, 3, 4]
    labels = list(range(5))
    assert cohens_kappa(a, near, labels, "quadratic") > cohens_kappa(a, far, labels, "quadratic")


def test_review_roundtrip(tmp_path):
    items = load_jsonl(DEV_PATH)
    path = tmp_path / "sheet.csv"
    assert export_sheet(items, path) == len(items)
    rows = read_sheet(path)
    assert list(rows[0].keys()) == sheet_columns()
    # Two reviewers: accept everything except one disagreement.
    for i, r in enumerate(rows):
        for n in (1, 2):
            r[f"r{n}_name"] = f"R{n}"
            r[f"r{n}_answer_correct"] = "yes"
            for f in ("bangla_ok", "syllabus_ok", "rubric_ok"):
                r[f"r{n}_{f}"] = "yes"
            r[f"r{n}_verdict"] = "accept"
        if i == 0:
            rows[0]["r2_verdict"] = "revise"
    rep = agreement_report(rows)
    assert rep["fields"]["verdict"]["n"] == len(rows)
    assert rep["n_needing_adjudication"] == 1
    assert final_verdict(rows[0]) is None
    updated, counts = apply_reviews(items, rows)
    assert counts["accept"] == len(rows) - 1 and counts["pending"] == 1
    assert updated[0]["verified"] is False and updated[1]["verified"] is True
    assert validate_items(updated) == []


def test_parse_judge_score():
    assert parse_judge_score('{"score": 2, "reason": "ok"}', 2) == 2
    assert parse_judge_score("Score: 5", 3) == 3  # clamped
    assert parse_judge_score("no idea", 2) is None


def test_calibration_pipeline(tmp_path):
    out = tmp_path / "run"
    run(DEV_PATH, make_adapter("mock-oracle"), out)
    sheet = tmp_path / "calib.csv"
    n = make_sheet(DEV_PATH, [out / "predictions.jsonl"], sheet, n=50)
    assert n > 0
    with open(sheet, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:  # pretend a teacher gave full marks
        r["human_score"] = r["max_marks"]
    with open(sheet, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SHEET_COLS)
        w.writeheader()
        w.writerows(rows)
    rep = run_calibration(sheet, Judge(make_adapter("mock-judge")), tmp_path / "scored.csv")
    assert rep["n"] == n
    assert rep["exact_agreement_pct"] == 100.0


def test_agreement_stats_shape():
    s = agreement_stats([1, 2, 0, 1], [1, 1, 0, 2], [1, 2, 2, 2])
    assert s["n"] == 4 and 0 <= s["exact_agreement_pct"] <= 100
    assert "per_mark_scale" in s
