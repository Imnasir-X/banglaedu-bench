import json

from banglaedu_bench.adapters import make_adapter
from banglaedu_bench.grounding import BundleGrounding, make_grounding
from banglaedu_bench.harness import run
from banglaedu_bench.judge import Judge
from banglaedu_bench.leaderboard import build_rows, collect, to_markdown
from banglaedu_bench.loader import DEV_PATH

BUNDLE = {
    "dataset": "nctb-data",
    "chapters": [{"id": "nctb:phy:c9-10:bn:ch02", "title": "গতি"}],
    "topics": [
        {
            "id": "nctb:phy:c9-10:bn:ch02:t06",
            "chapter_id": "nctb:phy:c9-10:bn:ch02",
            "number": "২.৬",
            "title": "ত্বরণ",
        },
        {
            "id": "nctb:phy:c9-10:bn:ch02:t07",
            "chapter_id": "nctb:phy:c9-10:bn:ch02",
            "number": "২.৭",
            "title": "গতির সমীকরণ",
        },
    ],
    "objectives": [
        {
            "id": "nctb:phy:c9-10:bn:ch02:o01",
            "chapter_id": "nctb:phy:c9-10:bn:ch02",
            "text": "গতির সমীকরণ ব্যবহার করে সমস্যা সমাধান করতে পারব।",
        }
    ],
}


def test_oracle_scores_100(tmp_path):
    s = run(DEV_PATH, make_adapter("mock-oracle"), tmp_path / "o")
    assert s["overall_pct_marks"] == 100.0
    assert s["n_errors"] == 0 and s["n_unparsed"] == 0
    assert (tmp_path / "o" / "predictions.jsonl").exists()


def test_constant_model_is_low(tmp_path):
    s = run(DEV_PATH, make_adapter("mock-constant"), tmp_path / "c")
    assert s["by"]["task_type"]["mcq"]["pct"] < 50


def test_without_judge_explanatory_parts_are_excluded(tmp_path):
    s = run(DEV_PATH, make_adapter("mock-oracle"), tmp_path / "nj")
    assert s["n_units_needing_judge"] > 0


def test_with_mock_judge_runs(tmp_path):
    s = run(
        DEV_PATH,
        make_adapter("mock-oracle"),
        tmp_path / "j",
        judge=Judge(make_adapter("mock-judge")),
    )
    assert s["n_units_needing_judge"] == 0
    assert s["overall_pct_marks"] > 90


def test_bundle_grounding_and_delta(tmp_path):
    bpath = tmp_path / "bundle.json"
    bpath.write_text(json.dumps(BUNDLE, ensure_ascii=False), encoding="utf-8")
    g = BundleGrounding(bpath, "topic")
    item = {"topic_id": "nctb:phy:c9-10:bn:ch02:t07"}
    assert "গতির সমীকরণ" in g.context(item, "x")
    gs = make_grounding("search", bundle=str(bpath))
    assert "ত্বরণ" in gs.context(item, "বস্তুর ত্বরণ কত")
    model = make_adapter("mock-grounded")
    base = run(DEV_PATH, model, tmp_path / "r" / "none", split_name="dev")
    mcp = run(DEV_PATH, model, tmp_path / "r" / "search", grounding=gs, split_name="dev")
    assert mcp["grounding_mode"] == "search"
    assert mcp["overall_pct_marks"] >= base["overall_pct_marks"]
    rows = build_rows(collect(tmp_path / "r"), "dev")
    assert rows and rows[0]["delta_mcp_search"] is not None
    md = to_markdown(rows, "dev")
    assert "MCP (search)" in md and "verified=false" in md


def test_resume_skips_done_items(tmp_path):
    out = tmp_path / "res"
    run(DEV_PATH, make_adapter("mock-oracle"), out, limit=3)
    s = run(DEV_PATH, make_adapter("mock-oracle"), out, limit=5)
    assert s["n_items"] == 5
