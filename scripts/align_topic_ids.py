"""Align this benchmark's topic ids with the shared nctb-data ids.

Usage (repo root):
  python scripts/align_topic_ids.py --shared <nctb-mcp>/data/physics-9-10-bn.json
      -> fills `suggested_shared_id` / `match_score` in data/topic_ids.csv (review by hand,
         then copy accepted suggestions into `shared_topic_id`)
  python scripts/build_seed.py
      -> rebuilds the splits; every row whose `shared_topic_id` is filled is applied
         (topic_id, concept_key, topic_id_status) and the test commitments are refreshed.

  python scripts/align_topic_ids.py --shared <physics-9-10-bn.json> --accept data/topic_alignment.csv
      -> copies the reviewed decisions in data/topic_alignment.csv into `shared_topic_id`
         (every id is checked to exist in the shared data; rows with an empty id stay provisional)

Matching is by title similarity within the same chapter (character trigrams), over sections and
subsections. It is a suggestion only: each accepted mapping is a reviewed row in
data/topic_alignment.csv, with who decided it.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banglaedu_bench.grounding import _char_ngrams, _title  # noqa: E402

MAP = ROOT / "data" / "topic_ids.csv"


def load_shared(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    topics = data.get("topics", data) if isinstance(data, dict) else data
    return [
        {"id": t["id"], "title": _title(t.get("title")), "chapter": t["id"].split(":ch")[1][:2]}
        for t in topics
        if isinstance(t, dict) and ":bn:" in t.get("id", "") and ":t" in t.get("id", "")
    ]


def suggest(shared_path: Path) -> None:
    shared = load_shared(shared_path)
    rows = list(csv.DictReader(MAP.open(encoding="utf-8")))
    for r in rows:
        ch = f"{int(r['chapter']):02d}"
        if any(s["id"] == r["topic_id"] for s in shared) and r["status"] == "ocr_observed":
            exact = next(s for s in shared if s["id"] == r["topic_id"])
            score = _sim(r["title_bn"], exact["title"])
            r["suggested_shared_id"], r["match_score"] = exact["id"], f"{score:.2f} (same id)"
            if score >= 0.5:  # same section number and matching title: identity mapping
                r["shared_topic_id"] = exact["id"]
            continue
        cands = [s for s in shared if s["chapter"] == ch]
        best = max(cands, key=lambda s: _sim(r["title_bn"], s["title"]), default=None)
        if best:
            r["suggested_shared_id"] = best["id"]
            r["match_score"] = f"{_sim(r['title_bn'], best['title']):.2f} ({best['title']})"
    cols = list(rows[0].keys())
    for extra in ("suggested_shared_id", "match_score"):
        if extra not in cols:
            cols.append(extra)
    with MAP.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote suggestions for {len(rows)} topics to {MAP}; review, then fill shared_topic_id")


def accept(shared_path: Path, decisions: Path) -> None:
    shared_ids = {s["id"] for s in load_shared(shared_path)}
    rows = list(csv.DictReader(MAP.open(encoding="utf-8")))
    by_pid = {r["topic_id"]: r for r in rows}
    applied = left = 0
    for d in csv.DictReader(decisions.open(encoding="utf-8")):
        pid, sid = d["provisional_id"].strip(), d["shared_topic_id"].strip()
        if pid not in by_pid:
            raise SystemExit(f"{pid}: not in {MAP.name}")
        if sid and sid not in shared_ids:
            raise SystemExit(f"{pid} -> {sid}: id not in the shared data")
        r = by_pid[pid]
        r["shared_topic_id"] = sid
        r["suggested_shared_id"] = sid or r.get("suggested_shared_id", "")
        r["match_score"] = f"{d['decided_by']}: {d['note']}"
        applied += bool(sid)
        left += not sid
    with MAP.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"accepted {applied} mappings, {left} left provisional; now run scripts/build_seed.py")


def _sim(a: str, b: str) -> float:
    ga, gb = _char_ngrams(a), _char_ngrams(b)
    return len(ga & gb) / (len(ga | gb) or 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shared", type=Path)
    ap.add_argument("--accept", type=Path, help="reviewed decisions CSV (data/topic_alignment.csv)")
    a = ap.parse_args()
    if a.shared and a.accept:
        accept(a.shared, a.accept)
    elif a.shared:
        suggest(a.shared)
    else:
        ap.print_help()
