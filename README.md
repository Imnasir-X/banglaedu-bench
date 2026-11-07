# BanglaEdu Bench

An open benchmark that tests how well large language models answer **Bangladesh NCTB
curriculum questions in Bangla**. v0.1: **Class 9-10 Physics (পদার্থবিজ্ঞান)**, 2026
edition, in the SSC exam's own formats: MCQ, short answer and সৃজনশীল (creative)
questions with all four parts (ক জ্ঞান, খ অনুধাবন, গ প্রয়োগ, ঘ উচ্চতর দক্ষতা).

> **Status: v0.1 seed, not released.** 80 original items. None is human-verified yet
> (`verified=false`). Numbers produced now are harness demos, not results.

## Why

Existing Bangla benchmarks are mostly scraped MCQ banks or extractive QA over textbook
text. BanglaEdu Bench adds: original items with exact citations, NCTB topic ids shared
with the [nctb-mcp](../nctb-mcp) data layer, creative questions with marking rubrics, a
calibrated LLM judge, two-reviewer agreement, a private test split with a canary, and a
with-vs-without-MCP grounding comparison. See [docs/research.md](docs/research.md).

## Quick start

```bash
uv sync
uv run banglaedu-bench validate dev                 # schema + recompute numeric keys
uv run banglaedu-bench stats dev
uv run banglaedu-bench run --model mock-oracle --split dev     # offline, 100%
uv run banglaedu-bench run --model ollama:qwen2.5:7b --split dev   # free, local
uv run banglaedu-bench run --model ollama:qwen2.5:7b --split dev --grounding search \
    --mcp-bundle ../nctb-shared/data/physics-9-10/physics-9-10-bn.json
uv run banglaedu-bench leaderboard --split dev
```

No paid API is required. See [docs/running.md](docs/running.md) for Ollama, vLLM,
llama.cpp and OpenRouter free models.

## Contents

| Path | What |
|---|---|
| `src/banglaedu_bench/` | schema, scorers, adapters, judge, harness, MCP grounding, leaderboard, review and calibration tools |
| `data/dev/dev.jsonl` | public dev split (28 items) |
| `data/dev/test_commitments.txt` | SHA-256 of each private test item |
| `data/private/` | **private, gitignored**: test split (52), item sources, full review sheet |
| `data/topic_ids.csv` | the one topic-id mapping file (provisional → shared `nctb-data` ids) |
| `review/` | dev review sheet, judge-calibration template |
| `schema/item.schema.json` | item format |
| `hf/README.md` | Hugging Face dataset card draft |
| `docs/` | research, design, running, review workflow, licensing |
| `leaderboard/` | generated leaderboard (currently mock baselines only) |

## Seed set (v0.1)

| Chapter | MCQ | Short | Srijonshil | Total |
|---|---|---|---|---|
| 1 ভৌত রাশি এবং তাদের পরিমাপ | 4 | 3 | 0 | 7 |
| 2 গতি | 4 | 3 | 1 | 8 |
| 3 বল | 5 | 3 | 1 | 9 |
| 4 কাজ, ক্ষমতা ও শক্তি | 3 | 3 | 1 | 7 |
| 5 পদার্থের অবস্থা ও চাপ | 4 | 5 | 1 | 10 |
| 6 বস্তুর ওপর তাপের প্রভাব | 2 | 2 | 1 | 5 |
| 7 তরঙ্গ ও শব্দ | 3 | 2 | 1 | 6 |
| 8 আলোর প্রতিফলন | 2 | 1 | 1 | 4 |
| 9 আলোর প্রতিসরণ | 3 | 2 | 1 | 6 |
| 10 স্থির বিদ্যুৎ | 1 | 1 | 0 | 2 |
| 11 চল বিদ্যুৎ | 3 | 3 | 2 | 8 |
| 12 বিদ্যুতের চৌম্বক ক্রিয়া | 2 | 2 | 1 | 5 |
| 13 তেজস্ক্রিয়তা ও ইলেকট্রনিকস | 2 | 1 | 0 | 3 |
| **Total** | **38** | **31** | **11** | **80** (dev 28, test 52) |

57 calculations (10 MCQ, 25 short answers, 22 srijonshil parts) are recomputed from
stored Python expressions on every CI run.

## Development

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run python scripts/build_seed.py      # rebuild splits from data/private/source (owner only)
```

## Licence

Code: MIT ([LICENSE](LICENSE)). Data: to be decided by the owner, proposed CC BY 4.0
([docs/licensing.md](docs/licensing.md)). NCTB textbooks are © NCTB; this repository
contains no textbook text.

Canary: see [CANARY.txt](CANARY.txt).
