"""Primary and junior seeds stay unverified drafts."""

import importlib.util
from pathlib import Path

from banglaedu_bench.adapters import make_adapter
from banglaedu_bench.curriculum import coverage
from banglaedu_bench.harness import run
from banglaedu_bench.loader import COLLEGE_PATH, DEV_PATH, JUNIOR_PATH, PRIMARY_PATH, load_jsonl
from banglaedu_bench.schema import validate_items
from banglaedu_bench.verify import check_items

ROOT = Path(__file__).resolve().parents[1]


def _school():
    path = ROOT / "scripts" / "build_school.py"
    spec = importlib.util.spec_from_file_location("build_school", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_school_files_match_the_builder_and_validate():
    module = _school()
    primary, junior = module.build_primary(), module.build_junior()
    assert load_jsonl(PRIMARY_PATH) == primary
    assert load_jsonl(JUNIOR_PATH) == junior
    for items, split in ((primary, "primary"), (junior, "junior")):
        assert validate_items(items) == []
        _n, errs = check_items(items)
        assert errs == []
        assert all(item["verified"] is False for item in items)
        assert all(item["split"] == split for item in items)
        assert all(item["schema_version"] == "0.2" for item in items)
        assert all(item["topic_id_status"] == "provisional" for item in items)
        assert all(item["source"]["license"] == "CC BY 4.0" for item in items)
        assert all(item["stream"] == "common" for item in items)
    assert all(item["class_level"] == [5] for item in primary)
    assert all(item["class_level"] == [6, 7, 8] for item in junior)
    assert {item["task_type"] for item in primary} <= {"mcq", "short_answer"}
    assert any(item["task_type"] == "srijonshil" for item in junior)


def test_school_oracle_is_not_a_pass(tmp_path):
    for path, split, band in (
        (PRIMARY_PATH, "primary", "primary"),
        (JUNIOR_PATH, "junior", "junior"),
    ):
        summary = run(path, make_adapter("mock-oracle"), tmp_path / split, split_name=split)
        assert summary["overall_pct_marks"] == 100.0
        assert summary["n_errors"] == 0
        assert summary["threshold"]["by_band"][band]["pass"] is None
        assert summary["threshold"]["comparable"] is False


def test_coverage_keeps_unwritten_subjects_empty():
    items = []
    for path in (DEV_PATH, COLLEGE_PATH, PRIMARY_PATH, JUNIOR_PATH):
        items.extend(load_jsonl(path))
    report = coverage(items)
    by_key = {(row["subject"], row["class_band"], row["stream"]): row for row in report["slots"]}
    assert by_key[("mathematics", "primary", "common")]["n_items"] > 0
    assert by_key[("elementary_science", "primary", "common")]["n_items"] > 0
    assert by_key[("general_science", "junior", "common")]["n_items"] > 0
    assert by_key[("ict", "junior", "common")]["n_items"] > 0
    for subject in ("islam", "hindu_religion", "buddhist_religion", "christian_religion"):
        assert by_key[(subject, "primary", "common")]["n_items"] == 0
    for subject in ("physical_education", "agriculture", "home_science", "fine_arts"):
        assert by_key[(subject, "junior", "common")]["n_items"] == 0
    for subject in ("career_education", "arabic"):
        assert by_key[(subject, "ssc", "common")]["n_items"] == 0
    assert report["n_slots_verified"] == 0
