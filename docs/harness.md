# Harness v0.2

The runner is the threshold for Bangladeshi school and college. The questions
catch up later. A model is measured the same way whether it is local or behind
an API.

## Who it can score

Class bands:

| Band | Classes | Tasks |
|---|---|---|
| primary | 5 | MCQ, short answer |
| junior | 6–8 | MCQ, short answer, সৃজনশীল |
| ssc | 9–10 | MCQ, short answer, সৃজনশীল |
| hsc | 11–12 (college) | MCQ, short answer, সৃজনশীল |

Streams are `common`, `science`, `commerce` (ব্যবসায় শিক্ষা) and `arts` (মানবিক).
The subject list is [subjects.md](subjects.md). College subjects of two papers
take paper 1 in class 11 and paper 2 in class 12. ICT at HSC is one paper.

Schema 0.1, the physics seed, still validates. New items use schema 0.2.

## Any model, one protocol

```text
mock-oracle
ollama:<model>          local
vllm:<model>            local
openai:<model>          OPENAI_API_KEY
groq:<model>            GROQ_API_KEY
openrouter:<model>      OPENROUTER_API_KEY
openai-compat:<model>   --base-url and --api-key-env
```

The locked protocol is temperature 0 and 1024 completion tokens. `--temperature`
and `--max-tokens` are for a debug. The run card sets `protocol.deviation` and
`threshold.comparable` to false when they differ.

The judge must be a different model from the one under test. The run refuses
otherwise. Written answers with no judge stay `needs_judge` and are left out of
the percent. A creative item whose every part still needs a judge is left out
the same way. An API or runtime error is `method: error` and is also left out.
It is not scored as a wrong answer.

A reply that repeats the canary GUID is contamination. `threshold.comparable`
is false for that run.

## What the report means

`summary.json` has:

- `by.class_band`, `by.stream`, `by.subject`, plus the older chapter and topic cuts
- `protocol` with the prompt hash, the endpoint, and `left_the_machine`
- `threshold.by_band` for primary, junior, SSC and college
- `threshold.overall_pct_ci95`, a 95% interval from resampling items
- `threshold.status` is `unverified_seed` while any item is still unchecked,
  and `not_comparable` when a checked set still broke the protocol
- `threshold.comparable`, false until every item in the run is two-reviewer
  verified and the protocol was followed

The pass line is 33 percent of the marks that were actually scored, the same
line as a board grade F. `pass` and `pass_pct` stay empty for a band until
every item of that band in the run is verified. Primary, junior, SSC and
college are all still empty, because no band is fully verified.

`banglaedu-bench coverage` shows every subject slot, including the empty ones.
An empty college slot is a missing question, not a model failure.

## What this is not

The public physics, college, primary, and junior items are unverified. Sending
the private test split to an API marks that run as having left the machine.
Do not treat either number as the bar a model must clear.

`scripts/run_local_baselines.py` is the local baseline entry. It asks for five
to eight models on this machine, temperature 0 and 1024 tokens, with and without
MCP, and it refuses a third-party URL. The public report keeps primary, junior,
SSC, and college in separate columns. A missing private file or a missing local
server writes `review/baselines_public_report.md` with those columns marked
`not run` or `no private items`. The committed private split is Class 9–10
physics, so the other bands have no private items yet.
