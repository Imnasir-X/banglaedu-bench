"""College seed, the chosen licence, the pass line, and the physics audit."""

import importlib.util
from pathlib import Path

from banglaedu_bench.adapters import make_adapter
from banglaedu_bench.curriculum import SUBJECTS
from banglaedu_bench.harness import run
from banglaedu_bench.loader import COLLEGE_PATH, DEV_PATH, JUNIOR_PATH, PRIMARY_PATH, load_jsonl
from banglaedu_bench.protocol import PASS_PCT, threshold_block
from banglaedu_bench.review import apply_reviews, read_sheet
from banglaedu_bench.schema import validate_items
from banglaedu_bench.verify import check_items

ROOT = Path(__file__).resolve().parents[1]
R1 = ROOT / "review" / "physics_dev_r1.csv"

COLLEGE_SUBJECTS = {
    "physics",
    "chemistry",
    "biology",
    "higher_mathematics",
    "accounting",
    "business_organization",
    "finance_banking_insurance",
    "history",
    "civics_good_governance",
    "logic",
    "economics",
    "bangla",
    "english",
    "ict",
}


def _builder():
    path = ROOT / "scripts" / "build_college.py"
    spec = importlib.util.spec_from_file_location("build_college", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_college_file_matches_the_builder_and_validates():
    items = load_jsonl(COLLEGE_PATH)
    assert _builder().build_items() == items
    assert validate_items(items) == []
    n, errs = check_items(items)
    assert errs == [] and n > 0
    assert {it["subject"] for it in items} == COLLEGE_SUBJECTS
    assert all(it["schema_version"] == "0.2" for it in items)
    assert all(it["verified"] is False for it in items)
    assert all(it["split"] == "college" for it in items)
    for subject in COLLEGE_SUBJECTS:
        rows = [it for it in items if it["subject"] == subject]
        if SUBJECTS[subject].hsc_papers == 2:
            assert any(it["class_level"] == [11] and it["paper"] == 1 for it in rows)
            assert any(it["class_level"] == [12] and it["paper"] == 2 for it in rows)
        else:
            assert {tuple(it["class_level"]) for it in rows} >= {(11,), (12,)}


def test_public_items_use_cc_by_4():
    for path in (DEV_PATH, COLLEGE_PATH, PRIMARY_PATH, JUNIOR_PATH):
        for item in load_jsonl(path):
            assert item["source"]["license"] == "CC BY 4.0"


def test_college_oracle_is_not_a_pass(tmp_path):
    summary = run(
        COLLEGE_PATH, make_adapter("mock-oracle"), tmp_path / "college", split_name="college"
    )
    assert summary["overall_pct_marks"] == 100.0
    assert summary["n_errors"] == 0
    assert summary["threshold"]["comparable"] is False
    assert summary["threshold"]["by_band"]["hsc"]["pass"] is None
    assert summary["threshold"]["by_band"]["hsc"]["n"] > 0
    assert summary["n_units_needing_judge"] > 0


def test_pass_mark_appears_only_when_the_band_is_checked():
    class Model:
        temperature = 0.0
        max_tokens = 1024

    checked = [
        {"verified": True, "class_level": [9, 10]},
        {"verified": True, "class_level": [9, 10]},
    ]
    high = threshold_block(checked, [], Model(), {"ssc": {"pct": 40.0, "n": 2}})
    assert high["by_band"]["ssc"]["pass"] is True
    assert high["by_band"]["ssc"]["pass_pct"] == PASS_PCT
    assert high["by_band"]["hsc"]["pass"] is None
    low = threshold_block(checked, [], Model(), {"ssc": {"pct": 20.0, "n": 2}})
    assert low["by_band"]["ssc"]["pass"] is False
    mixed = [
        {"verified": True, "class_level": [11]},
        {"verified": False, "class_level": [12]},
    ]
    held = threshold_block(mixed, [], Model(), {"hsc": {"pct": 90.0, "n": 2}})
    assert held["by_band"]["hsc"]["pass"] is None
    assert held["by_band"]["hsc"]["pass_pct"] is None


def test_physics_r1_does_not_verify_anything():
    rows = read_sheet(R1)
    dev = load_jsonl(DEV_PATH)
    assert len(rows) == len(dev) == 28
    assert {row["id"] for row in rows} == {item["id"] for item in dev}
    assert all(row["r1_name"] == "technical-audit" for row in rows)
    assert all(row["r2_name"] == "" for row in rows)
    assert all(row["r1_verdict"] == "revise" for row in rows)
    weak = next(row for row in rows if row["id"] == "bebench-phy-070")
    assert weak["r1_answer_correct"] == "no"
    updated, counts = apply_reviews(dev, rows)
    assert counts["accept"] == 0
    assert all(item["verified"] is False for item in updated)
