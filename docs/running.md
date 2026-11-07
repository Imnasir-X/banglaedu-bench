# Running models (no paid API needed)

```bash
uv sync                                   # Python 3.10+
uv run banglaedu-bench validate dev       # schema + recomputed numeric keys
uv run banglaedu-bench run --model mock-oracle --split dev   # offline smoke test (100%)
```

## Local and free options

| Option | Cost | Command |
|---|---|---|
| **Ollama** (local) | free, runs on your machine | `ollama pull qwen2.5:7b` then `uv run banglaedu-bench run --model ollama:qwen2.5:7b --split dev` |
| **vLLM** (local GPU) | free | `vllm serve <hf-model>` then `--model vllm:<hf-model>` |
| **llama.cpp / LM Studio** | free | start the OpenAI-compatible server, then `--model openai-compat:<name> --base-url http://localhost:8080/v1` |
| **OpenRouter `:free` models** | free tier, rate-limited; needs an account key | `export OPENROUTER_API_KEY=...` then `--model openrouter:<model>:free` |

Notes
* Models that handle Bangla reasonably at small sizes are worth trying first (for example
  Qwen 2.5/3, Gemma, Llama 3.x, TituLLM from Hishab). Check each model's licence.
* Do **not** send the private test split to a hosted API unless its terms say prompts are
  not retained or trained on. Use dev for hosted experiments; run test locally.
* `--workers` sets parallel requests (default 4); `--limit N` for a quick check; runs
  resume from `predictions.jsonl` if interrupted.

## With and without MCP

```bash
# baseline
uv run banglaedu-bench run --model ollama:qwen2.5:7b --split test
# grounded, live MCP server (stdio)
uv run banglaedu-bench run --model ollama:qwen2.5:7b --split test --grounding search \
    --mcp-command "node ../nctb-mcp/dist/cli.js"
# grounded, offline bundle
uv run banglaedu-bench run --model ollama:qwen2.5:7b --split test --grounding search \
    --mcp-bundle ../nctb-shared/data/physics-9-10/physics-9-10-bn.json
uv run banglaedu-bench leaderboard --split test
```

If the server's tools are named differently, pass `--mcp-search-tool`,
`--mcp-search-arg`, `--mcp-topic-tool`, `--mcp-topic-arg`.

## Judge

```bash
uv run banglaedu-bench run --model ollama:qwen2.5:7b --split test --judge ollama:gemma2:9b
```

Then calibrate it (`docs/review.md` § judge calibration) before publishing judged numbers.
