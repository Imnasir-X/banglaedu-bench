# BanglaEdu Bench v0.1: build report (2026-11-07)

Built locally; the public repo holds the code, the dev split and the test commitments only.
No Hugging Face upload, no paid API calls. Scope follows the owner spec (shared with the
nctb-mcp data layer): Class 9-10 Physics, Bangla.

## 1. Research findings and the gap

Full table with links: `docs/research.md`. In short:
* Existing Bangla evaluation sets are either general NLP (BLUB, BanglaBench), large MCQ
  exam banks (TituLLMs Bangla MMLU ~87.9k, BnMMLU ~134k, Global-MMLU bn), extractive or
  generated QA over textbook text (NCTB-QA 87.8k, NCTBench), or narrow (BEnQA 5,161
  science exam questions; PhysicsMate 1,834; P6Jiggasha 1,500 HSC MCQ; BanglaMATH).
  BEnQA's repo has no licence file.
* **Gap:** no openly licensed, original benchmark that has SSC physics in Bangla,
  srijonshil items with all four parts and rubrics, curriculum topic ids, two-reviewer
  agreement, a calibrated judge, a private test split with a canary, and a measured
  MCP-grounding delta. v0.1 builds all of that machinery.
* Licensing: NCTB textbook copyright vests in the Board (1983 Ordinance s.15(2)); the 2026
  book says "প্রকাশক কর্তৃক সর্বস্বত্ব সংরক্ষিত"; Copyright Act 2023 s.28 (60 years) and
  s.70 (exceptions only as the rules specify). So: original items only, citations to
  chapter/section ids, no textbook text.

## 2. What was built

* Python package `banglaedu-bench` 0.1.0 (stdlib only at runtime): schema validator,
  loader, Bangla normaliser, MCQ parser (ক/খ/গ/ঘ, A-D, 1-4, ১-৪), numeric extraction
  (Bangla digits, ×10ⁿ, superscripts, fractions) with tolerance, safe recomputation of
  keys, pluggable rubric-based LLM judge, adapters (mock-oracle/random/constant/grounded/
  judge; OpenAI-compatible for Ollama, vLLM, llama.cpp, OpenRouter), harness with resume
  and per-chapter/topic/level summaries, with/without-MCP grounding (live stdio MCP client
  or the `nctb-data` bundle), leaderboard (no-MCP, MCP search, Δ, MCP topic, per chapter),
  two-reviewer sheet + Cohen's kappa, judge calibration, test-split commitments.
* CLI: `validate, stats, run, leaderboard, review-export, review-agreement, review-apply,
  calib-sheet, calib-run, commit`.
* Tests: 50 pytest tests (49 run without the private split; all 50 with it), ruff lint and
  format clean, GitHub Actions workflow file (not pushed).
* Docs: README, design, running (free/local models), review workflow, licensing,
  research, HF card draft, JSON schema, CANARY.txt, MIT LICENSE.
* Topic ids: shared scheme `nctb:phy:c9-10:bn:chNN:tNN[:sNN]`; one mapping file
  `data/topic_ids.csv`, decisions in `data/topic_alignment.csv`. 77 of 80 items (all 28 dev)
  carry ids that exist in `nctb-data` 0.1.0 (ch 1-3 identity mappings; ch 4-13 mapped by the
  agent on 2026-11-07, 39 topics, reviewer to confirm). 3 test items on eye defects stay
  provisional (`ch09:t94`): the 2026 book has no section on eye defects.
* Baselines: mock models only (oracle 100%, random 4.1%, constant 5.5%, grounded-only
  5.5% → 100% with MCP search), proving the with/without-MCP plumbing. No real model runs.

## 3. Seed set

80 original items, all `verified=false`, version `0.1.0`, canary in each:
38 MCQ, 31 short answer (25 numeric), 11 srijonshil (44 parts, 22 numeric). 204 marks.
Dev 28 (public), test 52 (private). By chapter: 1:7, 2:8, 3:9, 4:7, 5:10, 6:5, 7:6, 8:4,
9:6, 10:2, 11:8, 12:5, 13:3. 57 calculations recomputed from Python expressions.
MCQ keys balanced across ক/খ/গ/ঘ.

## 4. Licence decisions the owner must make

See `docs/licensing.md`: (1) dataset licence (proposed CC BY 4.0); (2) terms for
third-party evaluation on the private test; (3) reviewer consent and credit;
(4) consistency with the `nctb-data` licence; (5) whether to ever seek NCTB permission
for official exercises or board questions.

## 5. Review the owner must do before release

See `docs/review.md`: two independent teacher reviews of all 80 items via the CSV sheet
(answer correct, Bangla, syllabus fit, rubric, verdict) with kappa reported; adjudication;
judge calibration on 50 human-scored answers; topic-id alignment for chapters 4-13; the
flagged-item list (specific heat and latent heat values, half-life in the 2026 syllabus,
mirror/lens sign conventions, friction ordering, Oersted spelling, etc.); 5-8 real
baselines with and without MCP; licence choice; then and only then publish.
