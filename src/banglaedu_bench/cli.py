"""Command-line interface: `banglaedu-bench <command> ...`."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections import Counter
from pathlib import Path

from . import __version__
from .loader import item_hash, load_items, load_jsonl, resolve_split, write_jsonl
from .schema import validate_items


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_validate(a) -> int:
    rc = 0
    for src in a.paths:
        items = load_jsonl(resolve_split(src))
        errs = validate_items(items)
        from .verify import check_items

        n_checked, verr = check_items(items)
        errs += verr
        print(f"{src}: {len(items)} items, {n_checked} keys recomputed, {len(errs)} errors")
        for e in errs:
            print("  -", e)
        rc |= bool(errs)
    return rc


def cmd_stats(a) -> int:
    from .curriculum import class_band, resolve_stream

    items = load_items(a.split)
    _print(
        {
            "n": len(items),
            "task_type": Counter(i["task_type"] for i in items),
            "class_band": Counter(class_band(i["class_level"]) for i in items),
            "subject": Counter(i["subject"] for i in items),
            "stream": Counter(resolve_stream(i) for i in items),
            "chapter": dict(sorted(Counter(i["chapter"]["number"] for i in items).items())),
            "difficulty": Counter(i["difficulty"] for i in items),
            "thinking_level": Counter(i["thinking_level"] for i in items),
            "verified": Counter(str(i["verified"]) for i in items),
            "mcq_key_labels": Counter(
                i["answer_key"]["label"] for i in items if i["task_type"] == "mcq"
            ),
        }
    )
    return 0


def cmd_subjects(_a) -> int:
    from .curriculum import SUBJECTS

    for subject in SUBJECTS.values():
        classes = sorted({c for offer in subject.offers for c in offer.classes})
        streams = []
        for offer in subject.offers:
            for stream in offer.streams:
                if stream not in streams:
                    streams.append(stream)
        print(
            f"{subject.key}\t{subject.name_bn}\tclasses={','.join(map(str, classes))}\t"
            f"streams={','.join(streams)}\thsc_papers={subject.hsc_papers}"
        )
    return 0


def cmd_coverage(a) -> int:
    from .curriculum import coverage

    report = coverage(load_items(a.split))
    _print({k: v for k, v in report.items() if k != "slots"})
    for slot in report["slots"]:
        if a.missing and slot["n_items"]:
            continue
        print(
            f"{slot['class_band']:8} {slot['stream']:10} {slot['subject']:28} "
            f"items={slot['n_items']} verified={slot['n_verified']}"
        )
    return 0


def _adapter_kwargs(a, spec: str = "") -> dict:
    kw = {}
    if getattr(a, "base_url", None):
        kw["base_url"] = a.base_url
    if getattr(a, "api_key_env", None):
        kw["api_key_env"] = a.api_key_env
    if spec.startswith("mock-"):
        return kw
    if getattr(a, "temperature", None) is not None:
        kw["temperature"] = a.temperature
    if getattr(a, "max_tokens", None) is not None:
        kw["max_tokens"] = a.max_tokens
    return kw


def cmd_run(a) -> int:
    from .adapters import make_adapter
    from .grounding import make_grounding
    from .harness import run
    from .judge import Judge

    model = make_adapter(a.model, **_adapter_kwargs(a, a.model))
    judge = Judge(make_adapter(a.judge, **_adapter_kwargs(a, a.judge))) if a.judge else None
    grounding = (
        make_grounding(
            a.grounding,
            bundle=a.mcp_bundle,
            mcp_command=shlex.split(a.mcp_command) if a.mcp_command else None,
            id_map_path=a.id_map,
            topic_tool=a.mcp_topic_tool,
            topic_arg=a.mcp_topic_arg,
            search_tool=a.mcp_search_tool,
            search_arg=a.mcp_search_arg,
        )
        if a.grounding != "none"
        else make_grounding("none")
    )
    safe = a.model.replace("/", "_").replace(":", "_")
    out = Path(a.out) / f"{a.split}__{safe}__{a.grounding}"
    try:
        summary = run(
            resolve_split(a.split),
            model,
            out,
            grounding=grounding,
            judge=judge,
            split_name=a.split if a.split in ("dev", "test") else Path(a.split).stem,
            workers=a.workers,
            limit=a.limit,
        )
    except ValueError as exc:
        print(exc)
        return 1
    finally:
        grounding.close()
    print(f"wrote {out}/predictions.jsonl and summary.json")
    _print(
        {
            "model": summary["model"],
            "grounding_mode": summary["grounding_mode"],
            "n_items": summary["n_items"],
            "overall_pct_marks": summary["overall_pct_marks"],
            "overall_pct_ci95": summary["threshold"]["overall_pct_ci95"],
            "by_band": summary["threshold"]["by_band"],
            "comparable": summary["threshold"]["comparable"],
            "threshold_status": summary["threshold"]["status"],
            "n_errors": summary["n_errors"],
            "n_unparsed": summary["n_unparsed"],
        }
    )
    return 0


def cmd_leaderboard(a) -> int:
    from .leaderboard import build_rows, collect, write

    rows = build_rows(collect(a.results), a.split)
    md, cs = write(rows, a.split, a.out)
    print(md.read_text(encoding="utf-8"))
    print(f"wrote {md} and {cs}")
    return 0


def cmd_review_export(a) -> int:
    from .review import export_sheet

    items = []
    for s in a.splits:
        items += load_items(s)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    n = export_sheet(items, a.out)
    print(f"wrote {n} rows to {a.out}")
    return 0


def cmd_review_agreement(a) -> int:
    from .review import agreement_report, read_sheet

    rep = agreement_report(read_sheet(a.sheet))
    _print(rep)
    if a.out:
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def cmd_review_apply(a) -> int:
    from .review import apply_reviews, read_sheet

    rows = read_sheet(a.sheet)
    path = resolve_split(a.split)
    items, counts = apply_reviews(load_jsonl(path), rows)
    errs = validate_items(items)
    if errs:
        print("refusing to write: items invalid after applying reviews", *errs, sep="\n  - ")
        return 1
    write_jsonl(a.out or path, items)
    _print(counts)
    return 0


def cmd_calib_sheet(a) -> int:
    from .calibration import make_sheet

    paths = [resolve_split(split) for split in a.split]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    n = make_sheet(paths, a.predictions, a.out, n=a.n, seed=a.seed)
    print(f"wrote {n} answers to {a.out} for human scoring (target 50)")
    return 0


def cmd_calib_run(a) -> int:
    from .adapters import make_adapter
    from .calibration import run_calibration
    from .judge import Judge

    rep = run_calibration(
        a.sheet, Judge(make_adapter(a.judge, **_adapter_kwargs(a, a.judge))), a.out_csv
    )
    _print(rep)
    if a.report:
        Path(a.report).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    if not rep.get("decision", {}).get("accepted"):
        print("judge not accepted")
        return 2
    return 0


def cmd_commit(a) -> int:
    items = load_jsonl(resolve_split(a.split))
    lines = [f"{it['id']}  sha256:{item_hash(it)}" for it in items]
    text = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {len(lines)} commitments to {a.out}")
    else:
        sys.stdout.write(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="banglaedu-bench", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("validate", help="schema-check items and recompute numeric keys")
    s.add_argument("paths", nargs="+", help="split names (dev/test) or JSONL paths")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("stats", help="counts by type, class band, subject, stream")
    s.add_argument("split", nargs="?", default="dev")
    s.set_defaults(fn=cmd_stats)

    s = sub.add_parser("subjects", help="list every subject the harness can score")
    s.set_defaults(fn=cmd_subjects)

    s = sub.add_parser("coverage", help="items present against every subject slot")
    s.add_argument("split", nargs="?", default="dev")
    s.add_argument("--missing", action="store_true", help="print only slots with no items")
    s.set_defaults(fn=cmd_coverage)

    s = sub.add_parser("run", help="evaluate a model")
    s.add_argument("--model", required=True, help="mock-oracle | ollama:<m> | openrouter:<m> ...")
    s.add_argument("--split", default="dev", help="dev | test | path to JSONL")
    s.add_argument("--judge", help="adapter spec for the written-answer judge")
    s.add_argument("--grounding", default="none", choices=["none", "search", "topic"])
    s.add_argument("--mcp-command", help='e.g. "npx -y nctb-mcp" (live stdio MCP server)')
    s.add_argument("--mcp-bundle", help="path to nctb-mcp bundled JSON (offline)")
    s.add_argument("--id-map", default="data/topic_ids.csv", help="provisional->shared topic ids")
    s.add_argument("--mcp-topic-tool", default="get_topic")
    s.add_argument("--mcp-topic-arg", default="topic_id")
    s.add_argument("--mcp-search-tool", default="search_curriculum")
    s.add_argument("--mcp-search-arg", default="query")
    s.add_argument("--base-url")
    s.add_argument("--api-key-env")
    s.add_argument(
        "--temperature", type=float, help="default 0. A different value is not comparable."
    )
    s.add_argument(
        "--max-tokens", type=int, help="default 1024. A different value is not comparable."
    )
    s.add_argument("--workers", type=int, default=4)
    s.add_argument("--limit", type=int)
    s.add_argument("--out", default="results")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("leaderboard", help="build Markdown/CSV leaderboard from results/")
    s.add_argument("--results", default="results")
    s.add_argument("--split", default="dev")
    s.add_argument("--out", default="leaderboard")
    s.set_defaults(fn=cmd_leaderboard)

    s = sub.add_parser("review-export", help="two-reviewer CSV sheet")
    s.add_argument("--splits", nargs="+", default=["dev", "test"])
    s.add_argument(
        "--out", default="data/private/review/review_sheet.csv", help="private: includes test items"
    )
    s.set_defaults(fn=cmd_review_export)

    s = sub.add_parser("review-agreement", help="percent agreement + Cohen's kappa")
    s.add_argument("sheet")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_review_agreement)

    s = sub.add_parser("review-apply", help="set verified=true where both reviewers accept")
    s.add_argument("sheet")
    s.add_argument("--split", required=True)
    s.add_argument("--out")
    s.set_defaults(fn=cmd_review_apply)

    s = sub.add_parser("calib-sheet", help="sample written answers for human scoring")
    s.add_argument("--split", nargs="+", default=["dev"])
    s.add_argument("--predictions", nargs="+", required=True)
    s.add_argument("--n", type=int, default=50)
    s.add_argument("--seed", type=int, default=13)
    s.add_argument("--out", default="data/private/review/judge_calibration_sheet.csv")
    s.set_defaults(fn=cmd_calib_sheet)

    s = sub.add_parser(
        "calib-run", help="score human-graded answers with the judge, report agreement"
    )
    s.add_argument("sheet")
    s.add_argument("--judge", required=True)
    s.add_argument("--base-url")
    s.add_argument("--api-key-env")
    s.add_argument("--out-csv")
    s.add_argument("--report")
    s.set_defaults(fn=cmd_calib_run)

    s = sub.add_parser("commit", help="SHA-256 commitments for a (private) split")
    s.add_argument("split")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_commit)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
