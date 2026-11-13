"""Run local baselines, or record why this machine cannot.

Five to eight local models, temperature 0, 1024 tokens, with and without MCP,
on the private test split. Mock adapters and third-party APIs are refused.
The public report lists primary, junior, SSC, and college separately.

Run from the repo root: uv run python scripts/run_local_baselines.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banglaedu_bench.baselines import (  # noqa: E402
    LOCAL_PROVIDERS,
    probe,
    public_report,
    write_blocked,
)
from banglaedu_bench.loader import TEST_PATH  # noqa: E402

COMMITMENTS = ROOT / "data" / "dev" / "test_commitments.txt"
REPORT = ROOT / "review" / "baselines_public_report.md"
STATUS = ROOT / "review" / "baselines_status.json"
# Filled in when this machine has local weights. Empty means the run is blocked.
MODELS: list[str] = []


def _bundle() -> Path | None:
    candidates = [
        ROOT.parent / "nctb-mcp" / "data" / "physics-9-10-bn.json",
        ROOT.parent / "nctb-shared" / "data" / "physics-9-10" / "physics-9-10-bn.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def main() -> int:
    status = probe(
        private_path=TEST_PATH,
        commitments=COMMITMENTS,
        models=MODELS,
        bundle=_bundle(),
    )
    if not status["ready"]:
        write_blocked(status, REPORT, STATUS)
        print("baselines not run")
        for reason in status["blocked"]:
            print(f"- {reason}")
        print(f"wrote {REPORT}")
        return 2
    _run(status)
    return 0


def _run(status: dict) -> None:
    """Score the private split on local servers. Not used while probe blocks."""
    from banglaedu_bench.adapters import make_adapter
    from banglaedu_bench.grounding import make_grounding
    from banglaedu_bench.harness import run
    from banglaedu_bench.protocol import MAX_TOKENS, TEMPERATURE

    bundle = status["mcp_bundle"]
    scores: dict[tuple[str, str], dict] = {}
    for spec in status["models"]:
        provider = spec.split(":", 1)[0]
        if provider not in LOCAL_PROVIDERS:
            raise SystemExit(f"refusing {spec}")
        model = make_adapter(spec, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
        modes = [("none", None)]
        if bundle:
            modes.append(("search", bundle))
        for mode, bundle_path in modes:
            grounding = (
                make_grounding("none")
                if bundle_path is None
                else make_grounding("search", bundle=bundle_path)
            )
            out = ROOT / "results" / "local-baselines" / f"{spec.replace(':', '_')}__{mode}"
            try:
                summary = run(
                    TEST_PATH,
                    model,
                    out,
                    grounding=grounding,
                    judge=None,
                    split_name="test",
                )
            finally:
                grounding.close()
            bands = summary.get("by", {}).get("class_band", {})
            scores[(spec, mode)] = {
                name: (bands.get(name) or {}).get("pct") for name in status["bands"]
            }
    status["ran"] = True
    status["ready"] = True
    REPORT.write_text(public_report(status, scores), encoding="utf-8")
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    raise SystemExit(main())
