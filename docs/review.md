# Review workflow and pre-release checklist

Nothing in v0.1 is human-verified. All 80 items ship `verified=false`. An item becomes
`verified=true` only through the two-reviewer process below.

## 1. Who reviews

Two reviewers per item, working independently, ideally:
* R1: an SSC physics teacher (or someone who has taught/marked SSC physics);
* R2: a second teacher or a strong physics graduate who is a native Bangla speaker.
An adjudicator (the owner or a third teacher) settles disagreements.

## 2. Item review (two-reviewer sheet)

1. Export: `uv run banglaedu-bench review-export` writes
   `data/private/review/review_sheet.csv` (all 80 items, **private: contains test
   items**). `review/review_sheet_dev.csv` holds the 28 dev items only.
2. Import into Google Sheets (File → Import → Upload; separator: comma; UTF-8). Share it
   privately. Hide the other reviewer's columns from each reviewer (or give each a copy)
   so ratings stay independent.
3. Each reviewer fills, per row:

   | column | values | question to answer |
   |---|---|---|
   | `rN_name` | initials | |
   | `rN_answer_correct` | yes / no | Is the key right? Redo every calculation by hand. |
   | `rN_bangla_ok` | yes / no | Is the Bangla natural, unambiguous, NCTB-style terminology? |
   | `rN_syllabus_ok` | yes / no | Within the 2026 Class 9-10 Physics syllabus (incl. the shortened SSC syllabus), right chapter/topic id? |
   | `rN_rubric_ok` | yes / no | Rubric fair, complete, matches NCTB marking practice? |
   | `rN_verdict` | accept / revise / reject | |
   | `rN_notes` | free text | exact corrections |

4. Download as CSV and compute agreement:
   `uv run banglaedu-bench review-agreement sheet.csv --out review/agreement_report.json`
   (percent agreement and Cohen's kappa for verdict and each yes/no field, plus how many
   rows need adjudication). Publish this report with the release.
5. Adjudicate rows where verdicts differ (`adjudicator`, `final_verdict`, `final_notes`).
6. Make the corrections in `data/private/source/` (never hand-edit the JSONL), rebuild
   with `uv run python scripts/build_seed.py`, re-export, and re-review revised items.
7. Apply verdicts:
   `uv run banglaedu-bench review-apply sheet.csv --split dev` (and `--split test`). An
   item is `verified=true` when both reviewers say accept and answer_correct=yes, or the
   adjudicator says accept. Release only verified items (`load_items(..., verified_only=True)`).

Target before publishing: verdict kappa ≥ 0.6 and answer-key agreement ≥ 95%. If lower,
tighten the guidelines and re-review rather than publishing.

## 3. Judge calibration (50 human-scored answers)

1. Run 2-3 real models on dev or test so there are real answers to grade.
2. `uv run banglaedu-bench calib-sheet --split test --predictions results/*/predictions.jsonl --n 50`
   samples 50 written answers (short explanatory answers and srijonshil ক/খ parts) into
   `data/private/review/judge_calibration_sheet.csv`.
3. A teacher fills `human_score` (integer, 0..max_marks) and `human_grader`, without seeing
   any judge output. Ideally a second teacher grades too, for a human-human baseline.
4. `uv run banglaedu-bench calib-run data/private/review/judge_calibration_sheet.csv --judge ollama:<model> --report review/judge_calibration_report.json`
5. Accept the judge if pass/fail kappa ≥ 0.6 and within-1-mark agreement ≥ 90%; otherwise
   change the judge model or prompt (bump `JUDGE_PROMPT_VERSION`) and repeat on fresh
   answers.

## 4. Items to look at first (flagged by the author)

| Item | Why |
|---|---|
| all chapter 4-13 items | topic ids were mapped by the agent (`data/topic_alignment.csv`); confirm the section, especially the rows marked "spans" |
| 3 test items on eye defects (ch 9) | the 2026 book has no eye-defects section; keep as out-of-book or drop |
| MCQ on water's specific heat (ch 6) | key uses the school value 4200 J kg⁻¹ K⁻¹; confirm the 2026 book uses the same |
| short answer on ice latent heat (ch 6) | uses 336000 J kg⁻¹; confirm the book's value |
| short answers on half-life (ch 13) and MCQ on half-life | confirm অর্ধায়ু is in the 2026 chapter 13 and in the shortened SSC syllabus |
| srijonshil on the concave mirror (ch 8) | magnification sign convention: key accepts 2 and −2; confirm the book's convention and wording |
| srijonshil on hypermetropia (ch 9) | sign convention in the lens formula; key f = 50 cm, P = +2 D |
| MCQ on friction (ch 3) | ordering static > sliding > rolling; option "তিনটিই সমান" |
| MCQ on significant figures (ch 1) | 0.00450 → 3; confirm the book teaches significant figures in 1.7 |
| MCQ on who discovered induction (ch 12) | Bangla spelling of Oersted (ওরস্টেড) |
| short answer "second law of reflection" (ch 8) | which law the book calls "second" |
| short answers with aliases | add any other accepted Bangla terms (e.g. synonyms used by teachers) |
| every srijonshil | rubric wording against real SSC marking; ঘ parts should demand genuine higher-order thinking |

## 5. Owner checklist before any public release

- [ ] Both reviewers have reviewed all items; agreement report published; only verified items released.
- [ ] Judge calibrated on 50 human-scored answers; report published next to judged scores.
- [ ] Topic ids aligned with `nctb-data` (no `t9x` provisional ids left) and `IDS.md` final.
- [ ] Dataset licence chosen (see `docs/licensing.md`) and written into every item and the card.
- [ ] Decide on the reviewer credit / consent wording (names in the card?).
- [ ] Baselines: 5-8 models, with and without MCP, on the private test split; per-topic table.
- [ ] Private split backed up privately; `data/private/` confirmed absent from git (`git status`, `git check-ignore`).
- [ ] Canary present in every released file; commitments regenerated after the last edit.
- [ ] Re-read the Hugging Face card draft (`hf/README.md`) and fill the TODOs.
- [ ] Only then: create the GitHub repo and the Hugging Face dataset (not done in v0.1).
