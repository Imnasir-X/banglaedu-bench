"""College review loop, judge bar, and the local-baseline gate."""

import csv
import importlib.util
import json
from pathlib import Path

from banglaedu_bench.baselines import probe, public_report, refusal
from banglaedu_bench.calibration import judge_decision
from banglaedu_bench.cli import main
from banglaedu_bench.loader import COLLEGE_PATH, JUNIOR_PATH, PRIMARY_PATH, load_jsonl
from banglaedu_bench.review import apply_reviews, read_sheet

ROOT = Path(__file__).resolve().parents[1]


def _script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_topic_gap_has_no_invented_shared_ids():
    rows = list(csv.DictReader((ROOT / "data" / "topic_gap.csv").open(encoding="utf-8-sig")))
    items = []
    for path in (COLLEGE_PATH, PRIMARY_PATH, JUNIOR_PATH):
        items.extend(load_jsonl(path))
    assert {row["item_id"] for row in rows} == {item["id"] for item in items}
    assert all(row["shared_topic_id"] == "" for row in rows)
    assert all(row["status"] == "no_nctb_data_bundle" for row in rows)
    assert (
        _script("record_topic_gap.py").gap_rows([COLLEGE_PATH, PRIMARY_PATH, JUNIOR_PATH]) == rows
    )


def test_author_recheck_does_not_verify(tmp_path):
    for sheet, path in (
        (ROOT / "review" / "college_r1.csv", COLLEGE_PATH),
        (ROOT / "review" / "primary_r1.csv", PRIMARY_PATH),
        (ROOT / "review" / "junior_r1.csv", JUNIOR_PATH),
    ):
        rows = read_sheet(sheet)
        items = load_jsonl(path)
        assert {row["id"] for row in rows} == {item["id"] for item in items}
        assert all(row["r1_name"] == "author-recheck" for row in rows)
        assert all(row["r1_verdict"] == "revise" for row in rows)
        assert all(row["r1_syllabus_ok"] == "no" for row in rows)
        assert all(row["r2_name"] == "" for row in rows)
        updated, counts = apply_reviews(items, rows)
        assert counts["accept"] == 0
        assert all(item["verified"] is False for item in updated)
    junior = read_sheet(ROOT / "review" / "junior_r1.csv")
    gap = next(row for row in junior if "She ___ a student." in row["question"])
    assert gap["r1_answer_correct"] == "no"
    blank = read_sheet(ROOT / "review" / "review_sheet_college.csv")
    assert all(row["r1_name"] == "" and row["r2_name"] == "" for row in blank)


def test_judge_decision_follows_the_written_bar():
    short = {"n": 12, "n_human_scored": 12, "pass_fail_kappa": 1.0, "within_1_mark_pct": 100.0}
    assert judge_decision(short)["accepted"] is False
    low_kappa = {"n_human_scored": 50, "pass_fail_kappa": 0.59, "within_1_mark_pct": 95.0}
    assert judge_decision(low_kappa)["accepted"] is False
    low_within = {"n_human_scored": 50, "pass_fail_kappa": 0.8, "within_1_mark_pct": 89.9}
    assert judge_decision(low_within)["accepted"] is False
    cleared = {"n_human_scored": 50, "pass_fail_kappa": 0.6, "within_1_mark_pct": 90.0}
    assert judge_decision(cleared)["accepted"] is True
    thin_compare = {
        "n": 10,
        "n_human_scored": 50,
        "pass_fail_kappa": 1.0,
        "within_1_mark_pct": 100.0,
    }
    assert judge_decision(thin_compare)["accepted"] is False


def test_pending_calibration_sheet_is_not_accepted():
    status = json.loads(
        (ROOT / "review" / "judge_calibration_status.json").read_text(encoding="utf-8")
    )
    rows = list(
        csv.DictReader(
            (ROOT / "review" / "judge_calibration_pending.csv").open(encoding="utf-8-sig")
        )
    )
    assert status["accepted"] is False
    assert status["private_split_used"] is False
    assert status["third_party_api"] is False
    assert status["real_local_models"] is False
    assert len(rows) == 50
    assert all(not str(row["human_score"]).strip() for row in rows)
    assert all(row["model"].startswith("mock-") for row in rows)


def test_calib_run_exits_when_the_judge_is_not_accepted(tmp_path):
    sheet = tmp_path / "empty.csv"
    sheet.write_text("unit_id,human_score,max_marks\n", encoding="utf-8")
    assert main(["calib-run", str(sheet), "--judge", "mock-judge"]) == 2


def test_baseline_gate_refuses_remote_and_missing_inputs(tmp_path):
    assert refusal("mock-oracle") == "mock adapters are not a baseline"
    assert "third-party" in refusal("openrouter:meta-llama/llama-3.1-8b-instruct:free")
    assert refusal("openai-compat:local", "https://api.example.com/v1")
    assert refusal("ollama:qwen2.5:7b") is None
    status = probe(
        private_path=tmp_path / "missing.jsonl",
        commitments=ROOT / "data" / "dev" / "test_commitments.txt",
        models=[],
        port_open_fn=lambda _host, _port: False,
    )
    assert status["ready"] is False
    assert status["ran"] is False
    assert status["private_test_present"] is False
    assert status["local_server"] is False
    assert status["private_items_by_band"]["ssc"] > 0
    assert status["private_items_by_band"]["primary"] == 0
    assert status["private_items_by_band"]["hsc"] == 0
    text = public_report(status)
    for label in ("primary", "junior", "SSC", "college"):
        assert label in text
    assert "not run" in text
    assert "no private items" in text
    saved = json.loads((ROOT / "review" / "baselines_status.json").read_text(encoding="utf-8"))
    assert saved["ran"] is False
    assert saved["third_party_api"] is False
    report = (ROOT / "review" / "baselines_public_report.md").read_text(encoding="utf-8")
    assert "not run" in report
    assert "SSC" in report and "college" in report
