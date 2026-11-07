import copy
import json
from pathlib import Path

import pytest

from banglaedu_bench import CANARY
from banglaedu_bench.loader import DEV_PATH, TEST_PATH, load_jsonl
from banglaedu_bench.schema import validate_item, validate_items
from banglaedu_bench.verify import check_items, safe_eval

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def dev():
    return load_jsonl(DEV_PATH)


@pytest.fixture(scope="module")
def all_items(dev):
    return dev + (load_jsonl(TEST_PATH) if TEST_PATH.exists() else [])


def test_dev_is_valid(dev):
    assert validate_items(dev) == []


def test_all_items_valid_and_unique(all_items):
    assert validate_items(all_items) == []
    assert len({it["id"] for it in all_items}) == len(all_items)


def test_seed_size_within_spec(all_items):
    # v0.1 seed: quality over volume, 60-100 items.
    if TEST_PATH.exists():
        assert 60 <= len(all_items) <= 100


def test_numeric_keys_recompute(all_items):
    n, errs = check_items(all_items)
    assert errs == []
    assert n > 0


def test_every_item_has_canary_version_topic_and_is_unverified(all_items):
    for it in all_items:
        assert it["canary"] == CANARY
        assert it["version"] == "0.1.0"
        assert it["topic_id"].startswith("nctb:phy:c9-10:bn:ch")
        assert it["verified"] is False  # nothing is human-reviewed yet
        assert it["source"]["type"] == "original_syllabus_aligned"


def test_no_past_paper_provenance(all_items):
    for it in all_items:
        cit = it["source"]["citation"].lower()
        assert "board" not in cit or "not copied" in cit


def test_srijonshil_has_four_parts(all_items):
    for it in all_items:
        if it["task_type"] == "srijonshil":
            assert [p["label"] for p in it["parts"]] == ["ক", "খ", "গ", "ঘ"]
            assert [p["marks"] for p in it["parts"]] == [1, 2, 3, 4]


def test_validator_rejects_bad_items(dev):
    good = next(it for it in dev if it["task_type"] == "mcq")
    bad = copy.deepcopy(good)
    bad["canary"] = "x"
    assert any("canary" in e for e in validate_item(bad))
    bad = copy.deepcopy(good)
    bad["source"]["type"] = "board_past_paper"
    assert any("permission" in e for e in validate_item(bad))
    bad = copy.deepcopy(good)
    bad["verified"] = True
    assert any("two recorded reviewers" in e for e in validate_item(bad))
    bad = copy.deepcopy(good)
    bad["options"][1]["text"] = bad["options"][0]["text"]
    assert validate_item(bad)


def test_safe_eval_blocks_code():
    assert safe_eval("0.5*9.8*3**2") == pytest.approx(44.1)
    with pytest.raises(ValueError):
        safe_eval("__import__('os').system('true')")


def test_test_split_is_gitignored():
    gi = (ROOT / ".gitignore").read_text()
    assert "data/private/" in gi


def test_commitments_match_private_split():
    if not TEST_PATH.exists():
        pytest.skip("private split not present")
    from banglaedu_bench.loader import item_hash

    lines = [
        ln
        for ln in (ROOT / "data/dev/test_commitments.txt").read_text().splitlines()
        if ln and not ln.startswith("#")
    ]
    expected = {f"{it['id']}  sha256:{item_hash(it)}" for it in load_jsonl(TEST_PATH)}
    assert set(lines) == expected


def test_dev_file_is_valid_json_lines():
    for line in DEV_PATH.read_text(encoding="utf-8").splitlines():
        json.loads(line)
