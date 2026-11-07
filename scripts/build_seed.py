"""Build the v0.1 seed from the private item sources.

The sources (data/private/source/seed_items.py and seed_srijonshil.py) hold every
item, test split included, so they live in the gitignored private folder. Only the
built dev split, the test commitments and the topic map are publishable.

Outputs
  data/dev/dev.jsonl               public dev split
  data/private/test.jsonl          private test split (gitignored)
  data/dev/test_commitments.txt    SHA-256 per test item (safe to publish)
  data/topic_ids.csv               topic id mapping, to align with nctb-data ids

Run from the repo root:  uv run python scripts/build_seed.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data" / "private" / "source"))

from seed_items import CHAPTERS, MCQ, SHORT, TOPICS  # noqa: E402
from seed_srijonshil import SRIJONSHIL  # noqa: E402

from banglaedu_bench import CANARY  # noqa: E402
from banglaedu_bench.loader import item_hash, write_jsonl  # noqa: E402
from banglaedu_bench.normalize import BN_LABELS  # noqa: E402
from banglaedu_bench.normalize import ascii_to_bn_digits as bn  # noqa: E402
from banglaedu_bench.schema import SRIJONSHIL_PARTS, validate_items  # noqa: E402
from banglaedu_bench.verify import check_items, safe_eval  # noqa: E402

VERSION = "0.1.0"
CREATED = "2026-11-07"
AUTHOR = "BanglaEdu Bench maintainers (drafted for Nasir Khan, GitHub Imnasir-X)"
CITATION = (
    "Original item written for BanglaEdu Bench v0.1 ({created}); aligned to the NCTB "
    "Class 9-10 Physics (পদার্থবিজ্ঞান) textbook, 2026 edition, chapter {ch} '{title}'. "
    "Not copied from any textbook exercise or education-board question paper."
)
SYLLABUS_REF = (
    "NCTB Class 9-10 subject structure (National Curriculum 2012 basis, effective 2025): "
    "https://nctb.portal.gov.bd/site/page/d61acf4b-951c-4a7c-abcd-666870078977"
)
DATA_LICENSE = "CC BY 4.0 (proposed; owner to confirm)"
DEV_EVERY = 3  # within each task type, index % 3 == 0 -> dev, else test


MAP_PATH = ROOT / "data" / "topic_ids.csv"


def load_mapping() -> dict[str, dict]:
    """Existing rows of data/topic_ids.csv (keeps human-accepted shared ids across rebuilds)."""
    if not MAP_PATH.exists():
        return {}
    with MAP_PATH.open(encoding="utf-8") as fh:
        return {r["topic_id"]: r for r in csv.DictReader(fh)}


MAPPING = load_mapping()


def provisional_id(ch: int, t: int) -> str:
    if (ch, t) not in TOPICS:
        raise KeyError(f"topic ({ch},{t}) missing from TOPICS")
    return f"nctb:phy:c9-10:bn:ch{ch:02d}:t{t:02d}"


def topic_id(ch: int, t: int) -> str:
    """Shared nctb-data id when a mapping has been accepted, else the provisional id."""
    pid = provisional_id(ch, t)
    shared = (MAPPING.get(pid, {}).get("shared_topic_id") or "").strip()
    return shared or pid


def topic_status(ch: int, t: int) -> str:
    pid = provisional_id(ch, t)
    if (MAPPING.get(pid, {}).get("shared_topic_id") or "").strip():
        return "aligned_nctb_data_draft"  # id exists in nctb-data v0.1.0 (itself verified=false)
    return TOPICS[(ch, t)][1]


def common(n: int, ch: int, t: int, task_type: str, split: str) -> dict:
    return {
        "id": f"bebench-phy-{n:03d}",
        "version": VERSION,
        "schema_version": "0.1",
        "canary": CANARY,
        "language": "bn",
        "class_level": [9, 10],
        "subject": "physics",
        "chapter": {"number": ch, "title_bn": CHAPTERS[ch], "edition": 2026},
        "topic_id": topic_id(ch, t),
        "concept_key": topic_id(ch, t).replace(":bn:", ":"),
        "topic_id_status": topic_status(ch, t),
        "task_type": task_type,
        "source": {
            "type": "original_syllabus_aligned",
            "citation": CITATION.format(created=CREATED, ch=ch, title=CHAPTERS[ch]),
            "author": AUTHOR,
            "created": CREATED,
            "license": DATA_LICENSE,
            "syllabus_reference": SYLLABUS_REF,
        },
        "verified": False,
        "review": {"reviewers": [], "final_verdict": "pending"},
        "split": split,
    }


def numeric_key(ref: str, num: tuple, aliases=None) -> tuple[dict, dict]:
    expr, unit, rel = num
    val = round(safe_eval(expr), 10)
    key = {
        "text": bn(ref),
        "aliases": [bn(a) for a in (aliases or [])],
        "numeric": {"value": val, "unit": unit, "rel_tol": rel, "abs_tol": 0.0},
    }
    if expr == "60/30":  # magnification: accept the sign convention that gives -2 too
        key["numeric"]["alt_values"] = [-val]
    if expr == "600/1000":  # fraction submerged: also accept 60 (per cent)
        key["numeric"]["alt_values"] = [val * 100]
    return key, {"method": "python_expression", "expression": expr}


def build() -> list[dict]:
    items: list[dict] = []
    n = 0
    rot = 0
    for i, d in enumerate(MCQ):
        n += 1
        opts, ans = list(d["opts"]), d["ans"]
        if d.get("rotate", True):  # balance keyed labels by cycling the answer through ক খ গ ঘ
            target = rot % 4
            rot += 1
            shift = (ans - target) % 4
            opts = opts[shift:] + opts[:shift]
            ans = target
        it = common(n, d["ch"], d["t"], "mcq", "dev" if i % DEV_EVERY == 0 else "test")
        it.update(
            question=bn(d["q"]),
            options=[{"label": BN_LABELS[k], "text": bn(o)} for k, o in enumerate(opts)],
            answer_key={"label": BN_LABELS[ans]},
            marking_rubric=[{"criterion": f"সঠিক বিকল্প ({BN_LABELS[ans]}) নির্বাচন", "marks": 1}],
            max_marks=1,
            explanation=bn(d["expl"]),
            difficulty=d["diff"],
            thinking_level=d["level"],
            answer_check=(
                {"method": "python_expression", "expression": d["expr"], "option_rel_tol": 0.01}
                if d.get("expr")
                else {"method": "author_physics_knowledge"}
            ),
        )
        items.append(it)
    for i, d in enumerate(SHORT):
        n += 1
        it = common(n, d["ch"], d["t"], "short_answer", "dev" if i % DEV_EVERY == 0 else "test")
        if "num" in d:
            key, chk = numeric_key(d["ref"], d["num"])
            rubric = [
                {"criterion": "সঠিক সূত্র বা পদ্ধতি", "marks": 1},
                {"criterion": "সঠিক চূড়ান্ত মান ও একক", "marks": 1},
            ]
            marks = 2
        else:
            key = {"text": bn(d["ref"]), "aliases": [bn(a) for a in d.get("aliases", [])]}
            chk = {"method": "author_physics_knowledge"}
            rubric = [{"criterion": f"সঠিক উত্তর: {bn(d['ref'])}", "marks": 1}]
            marks = 1
        it.update(
            question=bn(d["q"]),
            answer_key=key,
            marking_rubric=rubric,
            max_marks=marks,
            explanation=bn(d["ref"]),
            difficulty=d["diff"],
            thinking_level=d["level"],
            answer_check=chk,
        )
        items.append(it)
    for i, d in enumerate(SRIJONSHIL):
        n += 1
        it = common(n, d["ch"], d["t"], "srijonshil", "dev" if i % DEV_EVERY == 0 else "test")
        parts = []
        for (label, level, marks), (q, ref, aliases, num, rubric) in zip(
            SRIJONSHIL_PARTS, d["parts"], strict=False
        ):
            if num:
                key, chk = numeric_key(ref, num, aliases)
            else:
                key = {"text": bn(ref), "aliases": [bn(a) for a in (aliases or [])]}
                chk = {"method": "author_physics_knowledge"}
            parts.append(
                {
                    "label": label,
                    "thinking_level": level,
                    "marks": marks,
                    "question": bn(q),
                    "answer_key": key,
                    "marking_rubric": [{"criterion": bn(c), "marks": m} for c, m in rubric],
                    "answer_check": chk,
                }
            )
        it.update(
            question=bn(d["stim"]),
            parts=parts,
            answer_key={"parts": {p["label"]: p["answer_key"]["text"] for p in parts}},
            marking_rubric=[
                {
                    "criterion": f"({p['label']}) {p['thinking_level']}: see part rubric",
                    "marks": p["marks"],
                }
                for p in parts
            ],
            max_marks=10,
            explanation=bn(d["expl"]),
            difficulty=d["diff"],
            thinking_level="higher_ability",
            answer_check={"method": "per_part"},
        )
        items.append(it)
    return items


def main() -> int:
    items = build()
    errs = validate_items(items)
    n_checked, verr = check_items(items)
    errs += verr
    if errs:
        print("\n".join(errs))
        return 1
    dev = [it for it in items if it["split"] == "dev"]
    test = [it for it in items if it["split"] == "test"]
    write_jsonl(ROOT / "data" / "dev" / "dev.jsonl", dev)
    write_jsonl(ROOT / "data" / "private" / "test.jsonl", test)
    (ROOT / "data" / "dev" / "test_commitments.txt").write_text(
        "# SHA-256 of each private test item's canonical JSON (banglaedu_bench.loader.item_hash).\n"
        f"# {CANARY}\n" + "".join(f"{it['id']}  sha256:{item_hash(it)}\n" for it in test),
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for it in items:
        counts[it["topic_id"]] = counts.get(it["topic_id"], 0) + 1
    cols = [
        "topic_id",
        "chapter",
        "topic_no",
        "title_bn",
        "status",
        "shared_topic_id",
        "n_items",
        "suggested_shared_id",
        "match_score",
    ]
    with MAP_PATH.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for (ch, t), (title, _status) in sorted(TOPICS.items()):
            pid = provisional_id(ch, t)
            old = MAPPING.get(pid, {})
            w.writerow(
                {
                    "topic_id": pid,
                    "chapter": ch,
                    "topic_no": t,
                    "title_bn": title,
                    "status": topic_status(ch, t),
                    "shared_topic_id": old.get("shared_topic_id", ""),
                    "n_items": counts.get(topic_id(ch, t), 0),
                    "suggested_shared_id": old.get("suggested_shared_id", ""),
                    "match_score": old.get("match_score", ""),
                }
            )
    print(f"built {len(items)} items: dev={len(dev)} test={len(test)}; {n_checked} keys recomputed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
