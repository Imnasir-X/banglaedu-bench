"""Catalog, schema 0.2 and the run card."""

import json

from banglaedu_bench import CANARY
from banglaedu_bench.adapters import make_adapter
from banglaedu_bench.curriculum import (
    BAND_ID,
    STREAMS,
    SUBJECTS,
    catalog_slots,
    class_band,
    coverage,
    render_subjects_markdown,
)
from banglaedu_bench.harness import run, summarize
from banglaedu_bench.judge import Judge
from banglaedu_bench.loader import DEV_PATH
from banglaedu_bench.prompts import system_for
from banglaedu_bench.protocol import left_the_machine
from banglaedu_bench.schema import validate_item, validate_items

ROOT_DOCS = DEV_PATH.parents[2] / "docs" / "subjects.md"


def _representative(subject):
    """One legal class list, preferring college when the subject is taught there."""

    def rank(offer):
        if 11 in offer.classes or 12 in offer.classes:
            return 0
        if 9 in offer.classes:
            return 1
        if 6 in offer.classes:
            return 2
        return 3

    offer = sorted(subject.offers, key=rank)[0]
    stream = offer.streams[0]
    if 11 in offer.classes or 12 in offer.classes:
        paper = 1 if subject.hsc_papers == 2 else None
        classes = [11] if 11 in offer.classes else [12]
        return classes, stream, paper
    for group in ((9, 10), (6, 7, 8), (5,)):
        if all(number in offer.classes for number in group):
            return list(group), stream, None
    return [offer.classes[0]], stream, None


def _item(subject, classes, stream, paper=None, task="mcq", suffix=""):
    band = class_band(classes)
    assert band is not None
    language = "en" if subject.key == "english" else "bn"
    item = {
        "id": f"bebench-{subject.topic_code}-{BAND_ID[band]}-001",
        "version": "0.2.0",
        "schema_version": "0.2",
        "canary": CANARY,
        "language": language,
        "class_level": classes,
        "subject": subject.key,
        "stream": stream,
        "chapter": {"number": 1, "title_bn": "ভূমিকা", "edition": "2026"},
        "topic_id": f"nctb:{subject.topic_code}:{BAND_ID[band]}:{language}:ch01:t01",
        "task_type": task,
        "question": f"নমুনা {subject.key} {band} {stream} {classes}{suffix}",
        "options": [
            {"label": "ক", "text": "প্রথম"},
            {"label": "খ", "text": "দ্বিতীয়"},
            {"label": "গ", "text": "তৃতীয়"},
            {"label": "ঘ", "text": "চতুর্থ"},
        ],
        "answer_key": {"label": "ক"},
        "marking_rubric": [{"criterion": "সঠিক বিকল্প", "marks": 1}],
        "max_marks": 1,
        "explanation": "নমুনা ব্যাখ্যা",
        "difficulty": "easy",
        "thinking_level": "knowledge",
        "source": {
            "type": "original_syllabus_aligned",
            "citation": "harness fixture, not a released question",
            "author": "harness",
            "created": "2026-11-13",
            "license": "CC BY 4.0 (proposed; owner to confirm)",
        },
        "answer_check": {"method": "author_subject_knowledge"},
        "verified": False,
        "review": {"reviewers": []},
        "split": "dev",
    }
    if paper is not None:
        item["paper"] = paper
    return item


def test_every_subject_has_a_valid_item():
    items = []
    for subject in SUBJECTS.values():
        classes, stream, paper = _representative(subject)
        item = _item(subject, classes, stream, paper)
        assert validate_item(item) == [], subject.key
        items.append(item)
    assert validate_items(items) == []


def test_streams_and_college_are_complete():
    slots = catalog_slots()

    def keys(band, stream):
        return {
            row["subject"] for row in slots if row["class_band"] == band and row["stream"] == stream
        }

    assert {"bangla", "english", "ict"} <= keys("hsc", "common")
    assert "geography" in keys("hsc", "science")
    assert "geography" in keys("hsc", "arts")
    assert "geography" in keys("hsc", "commerce")
    assert "economics" in keys("hsc", "commerce")
    assert "islam" in keys("hsc", "arts")
    assert {"physics", "chemistry", "biology", "higher_mathematics"} <= keys("hsc", "science")
    assert {
        "accounting",
        "business_organization",
        "finance_banking_insurance",
        "production_marketing",
    } <= keys("hsc", "commerce")
    assert {
        "history",
        "civics_good_governance",
        "logic",
        "sociology",
        "social_work",
        "psychology",
        "islamic_history",
    } <= keys("hsc", "arts")
    assert {"physics", "chemistry"} <= keys("ssc", "science")
    assert {"accounting", "finance_and_banking", "business_entrepreneurship"} <= keys(
        "ssc", "commerce"
    )
    assert {"history", "geography", "civics", "economics"} <= keys("ssc", "arts")
    assert "general_science" in keys("ssc", "arts")
    assert "general_science" in keys("ssc", "commerce")
    assert {"bangla", "english", "mathematics", "elementary_science"} <= keys("primary", "common")
    assert set(STREAMS) == {"common", "science", "commerce", "arts"}


def test_primary_rejects_srijonshil_and_college_paper_is_strict():
    math = SUBJECTS["mathematics"]
    item = _item(math, [5], "common", task="srijonshil")
    assert any("primary does not use" in err for err in validate_item(item))

    accounting = SUBJECTS["accounting"]
    missing = _item(accounting, [11], "commerce")
    assert any("paper 1" in err for err in validate_item(missing))
    both_years = _item(accounting, [11, 12], "commerce", paper=1)
    assert any("paper 1" in err for err in validate_item(both_years))
    bad_id = _item(accounting, [12], "commerce", paper=2, suffix=" bad id")
    bad_id["id"] = "bebench-acct-c12-001"
    assert any("id must look like" in err for err in validate_item(bad_id))
    ok = _item(accounting, [12], "commerce", paper=2, suffix=" paper 2")
    assert class_band([12]) == "hsc"
    assert ok["id"] == f"bebench-acct-{BAND_ID['hsc']}-001"
    assert validate_item(ok) == []

    physics = _item(SUBJECTS["physics"], [9, 10], "arts")
    assert any("not offered" in err for err in validate_item(physics))


def test_prompts_name_the_band_and_subject():
    college = _item(SUBJECTS["accounting"], [11], "commerce", paper=1)
    text = system_for(college)
    assert "কলেজ" in text or "এইচএসসি" in text
    assert "হিসাববিজ্ঞান" in text
    assert "পত্র: 1" in text
    english = _item(SUBJECTS["english"], [5], "common")
    assert "Answer in English" in system_for(english)
    primary = _item(SUBJECTS["mathematics"], [5], "common")
    assert "পঞ্চম" in system_for(primary)


def test_subjects_doc_matches_the_catalog():
    assert ROOT_DOCS.read_text(encoding="utf-8") == render_subjects_markdown()


def test_dev_coverage_is_physics_only():
    items = [json.loads(line) for line in DEV_PATH.read_text(encoding="utf-8").splitlines() if line]
    report = coverage(items)
    assert report["by_band"]["hsc"]["with_items"] == 0
    assert report["by_band"]["primary"]["with_items"] == 0
    filled = [s for s in report["slots"] if s["n_items"]]
    assert {(s["subject"], s["class_band"], s["stream"]) for s in filled} == {
        ("physics", "ssc", "science")
    }
    assert filled[0]["n_items"] == 28
    assert filled[0]["n_verified"] == 0


def test_run_card_keeps_bands_and_refuses_the_same_judge(tmp_path):
    summary = run(DEV_PATH, make_adapter("mock-oracle"), tmp_path / "oracle")
    assert summary["by"]["class_band"]["ssc"]["pct"] == 100.0
    assert summary["by"]["class_band"]["hsc"]["n"] == 0
    assert summary["threshold"]["comparable"] is False
    assert summary["threshold"]["by_band"]["ssc"]["pass"] is None
    assert summary["threshold"]["by_band"]["hsc"]["pass"] is None
    assert summary["threshold"]["overall_pct_ci95"] == [100.0, 100.0]
    assert summary["protocol"]["left_the_machine"] is False
    assert summary["protocol"]["deviation"] is False
    try:
        run(
            DEV_PATH,
            make_adapter("mock-oracle"),
            tmp_path / "same",
            judge=Judge(make_adapter("mock-oracle")),
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_errors_are_not_counted_as_wrong_answers():
    scored = {
        "task_type": "mcq",
        "chapter": 1,
        "topic_id": "t",
        "thinking_level": "knowledge",
        "score": 1,
        "max_marks": 1,
        "method": "exact",
        "class_band": "hsc",
        "subject": "accounting",
        "stream": "commerce",
    }
    failed = {**scored, "score": 0, "method": "error", "topic_id": "e"}
    waiting = {
        **scored,
        "method": "parts",
        "score": 0,
        "max_marks": 0,
        "topic_id": "w",
        "n_parts_needing_judge": 4,
    }
    summary = summarize([scored, failed, waiting])
    assert summary["overall_pct_marks"] == 100.0
    assert summary["n_errors"] == 1
    assert summary["n_scored_items"] == 1
    assert summary["n_units_needing_judge"] == 4


def test_checked_items_on_protocol_are_comparable_until_the_canary_leaks():
    from banglaedu_bench import CANARY_GUID
    from banglaedu_bench.protocol import threshold_block

    class Model:
        temperature = 0.0
        max_tokens = 1024

    items = [{"verified": True}, {"verified": True}]
    clean = [
        {"method": "exact", "score": 1, "max_marks": 1, "output": "ক"},
        {"method": "exact", "score": 0, "max_marks": 1, "output": "খ"},
    ]
    block = threshold_block(items, clean, Model(), {"ssc": {"pct": 50.0, "n": 2}})
    assert block["status"] == "checked"
    assert block["comparable"] is True
    assert block["by_band"]["hsc"]["n"] == 0
    assert block["by_band"]["ssc"]["pct"] == 50.0
    leaked = [{**clean[0]}, {**clean[1], "output": f"seen {CANARY_GUID}"}]
    dirty = threshold_block(items, leaked, Model(), {})
    assert dirty["status"] == "not_comparable"
    assert dirty["comparable"] is False
    assert any("canary" in reason for reason in dirty["reasons"])


def test_remote_endpoint_is_marked():
    class Remote:
        base_url = "https://api.openai.com/v1"
        temperature = 0.0
        max_tokens = 1024

    assert left_the_machine(Remote()) is True

    class Local:
        base_url = "http://localhost:11434/v1"

    assert left_the_machine(Local()) is False
