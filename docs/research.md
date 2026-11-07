# Research notes: existing Bangla benchmarks, the gap, licensing, contamination

Compiled 2026-11-07. Every claim links to the page it came from. "Not verified" marks
what I could not confirm from a primary source.

## 1. Existing Bangla / Bengali evaluation resources

| Resource | What it is | Size | Source of questions | Licence (as found) | Relevance to BanglaEdu Bench |
|---|---|---|---|---|---|
| **BLUB** (with BanglaBERT) | Bangla NLU suite (classification, NER, NLI, extractive QA) | 4 tasks | Annotated NLP corpora | see paper | Encoder-era NLU, not curriculum QA. [arXiv 2101.00204](https://arxiv.org/abs/2101.00204) |
| **BanglaBench** (COLING 2025) | LLMs vs fine-tuned models on Bangla NLP tasks | — | Existing NLP datasets | see repo | General NLP tasks, not school curriculum. [GitHub](https://github.com/satak100/BanglaBench) |
| **BEnQA** | Parallel Bangla/English science exam questions from the Bangladeshi national curriculum | 5,161 | Grade-school exam questions | **No licence file in the repo** (GitHub API reports none); a third-party catalogue lists CC BY-NC-SA 4.0 (not confirmed with the authors) | Closest prior work; MCQ-centred, public (contamination-exposed), no per-item provenance or rubrics. [arXiv 2403.10900](https://arxiv.org/abs/2403.10900), [GitHub](https://github.com/sheikhshafayat/BEnQA) |
| **TituLLMs Bangla MMLU** (Hishab) | 4-option MCQ from job, BCS and admission exams; wired into lm-evaluation-harness (`lm_eval/tasks/bangla`) | ~87.9k | Exam questions | see HF card | Broad exam MCQ, not SSC-curriculum mapped, MCQ only. [arXiv 2502.11187](https://arxiv.org/abs/2502.11187), [HF](https://huggingface.co/datasets/hishab/titulm-bangla-mmlu) |
| **BnMMLU** (ACL Findings 2026) | Multi-domain Bengali MCQ | ~134k, 41 subjects | Academic and professional domains | Gated; card marks it preliminary | MCQ only; no curriculum topic ids or written answers. [ACL](https://aclanthology.org/2026.findings-acl.593/), [HF](https://huggingface.co/datasets/samanjoy2/BnMMLU) |
| **Global-MMLU (bn)** | MMLU translated into Bengali | MMLU-size | Translated from English | Apache-2.0 | Translated Western content, not Bangladeshi curriculum. [HF](https://huggingface.co/datasets/CohereLabs/Global-MMLU) |
| **BLUCK** | Bengali linguistics and culture MCQ | — | Native sources | see paper | Culture/linguistics, not science. [arXiv 2505.21092](https://arxiv.org/html/2505.21092v2) |
| **NCTB-QA** | Extractive QA over NCTB textbooks | 87.8k | Textbook passages | CC BY-NC 4.0 (as listed) | Span extraction that reproduces textbook text. [arXiv 2603.05462](https://arxiv.org/abs/2603.05462) |
| **NCTBench** (ShihabReza/nctb-qa) | RAG / extractive QA from NCTB pilot textbooks | — | Generated with an LLM via Together AI from textbook chunks | CC BY 4.0 (as stated on the card) | Generated, extractive; ships textbook-derived text. [HF](https://huggingface.co/datasets/ShihabReza/nctb-qa) |
| **PhysicsMate** | Bengali Class 9-10 physics QA built on a knowledge graph | 1,834 | NCTB 9-10 physics | not stated | Same subject; aimed at model adaptation, not a held-out benchmark. [arXiv 2610.00664](https://arxiv.org/abs/2610.00664) |
| **P6Jiggasha** | Bangla HSC physics MCQ | 1,500 | Guide books and test papers | not stated | HSC, MCQ only, third-party guide material. [PDF](https://aclanthology.org/2025.banglalp-1.16.pdf) |
| **BanglaMATH** | Bangla math word problems, grades 6-8 | ~1.7k | Workbooks | research-only (as listed) | Math only, lower grades. [arXiv 2510.12836](https://arxiv.org/abs/2510.12836) |
| **SOMADHAN** | Bengali math word problems | — | — | see paper | Math reasoning only. [arXiv 2505.21354](https://arxiv.org/abs/2505.21354) |
| **NCTB_MCQ** (nayemislamzr) | NCTB MCQ collection on Hugging Face | — | not documented | not stated | Provenance unclear. |

## 2. The gap BanglaEdu Bench fills

None of the above combines all of these:

1. **Curriculum-addressable items.** Every item carries a stable topic id shared with the
   `nctb-data` layer (`nctb:phy:c9-10:bn:ch02:t07`), so scores break down by chapter and
   section and can be joined to the NCTB MCP server.
2. **The SSC exam's own formats, including সৃজনশীল (creative) questions** with the four
   NCTB thinking levels (জ্ঞান, অনুধাবন, প্রয়োগ, উচ্চতর দক্ষতা) and marks 1/2/3/4. Prior
   work is MCQ-centred or extractive.
3. **Marking rubrics and a calibrated judge.** Written answers are graded against a
   per-item rubric by an LLM judge whose agreement with 50 human-scored answers is
   measured and published.
4. **Clean provenance.** Original items only, each with an exact citation; no board
   papers, no guide books, no textbook text mirrored.
5. **Contamination control.** Private test split with a canary and SHA-256 commitments;
   only dev is released.
6. **Two-reviewer verification with published agreement** (percent agreement and
   Cohen's kappa); `verified=false` until two humans accept an item.
7. **Grounding delta.** The same models are run with and without curriculum grounding
   from the NCTB MCP server, and the accuracy difference is published.

## 3. Licensing of question sources

* **NCTB textbooks.** Copyright in textbooks published by the Board vests in the Board
  under the National Curriculum and Text-Book Board Ordinance 1983, s.15(2)
  ([bdlaws](https://bdlaws.minlaw.gov.bd/act-print-656/section-print-8898.html)); the
  Ordinance was later replaced by the NCTB Act 2018 (successor provision not checked).
  The 2026 Physics book's imprint page reads "প্রকাশক কর্তৃক সর্বস্বত্ব সংরক্ষিত" (all rights
  reserved by the publisher; PDF page 3 of the copy in the workspace). Free distribution
  does not make the books openly licensed. Government works stay in copyright for 60 years
  after first publication: Copyright Act 2023, s.28
  ([bdlaws](https://bdlaws.minlaw.gov.bd/act-1452/section-52654.html)).
* **Exceptions.** Copyright Act 2023, s.70: acts done for the purposes and under the
  conditions specified in the rules do not infringe
  ([bdlaws](http://bdlaws.minlaw.gov.bd/act-1452/section-52696.html)). I did not find the
  rules, so whether s.70 covers a public ML dataset is unresolved. **Not legal advice.**
* **Board past papers (SSC/HSC).** Set by the education boards; no open licence was found.
  Treat them as all-rights-reserved. The schema refuses `board_past_paper` and
  `textbook_exercise` items unless `source.permission` documents written permission.
* **Third-party guide books and coaching MCQ banks.** Commercial and copyrighted; excluded.
* **Decision for v0.1.** Only original items written to the syllabus (facts, formulas and
  curricular concepts are not copyrightable; the wording is ours). The `nctb-data` layer
  likewise stores structure, ids and page pointers, not book text.

## 4. Contamination concerns

* Public Bangla exam QA (BEnQA, Bangla MMLU, guide-book MCQ sites) is crawlable and likely
  in pre-training corpora; board questions are reprinted across thousands of coaching
  sites, so "past paper" benchmarks measure memorisation as much as ability.
* Canary strings let crawler operators filter benchmark files and let researchers probe
  for leakage; the BIG-bench convention is a fixed sentence plus a GUID
  ([BIG-bench docs](https://github.com/google/BIG-bench/blob/main/docs/doc.md)). Canaries
  are a request, not a guarantee: the pre-RLHF GPT-4 base model was reported to reproduce
  the BIG-bench canary
  ([LessWrong](https://www.lesswrong.com/posts/kSmHMoaLKGcGgyWzs/big-bench-canary-contamination-in-gpt-4)).
  NIST AI 800-2 (initial public draft) also discusses canaries and hidden test data as
  contamination controls.
* Hence: a private test split that is never published, a public dev split for
  development, commitments (hashes) so the private split can be audited later, and
  refreshed test items for each release. See `docs/design.md` §6.

## 5. Curriculum context (why Class 9-10 Physics, 2026 edition)

Bangladesh returned to the National Curriculum 2012 structure from the 2025 academic year,
with science/humanities/business groups restored in Classes 9-10 and a shortened syllabus
for the 2026 SSC
([Daily Star, 1 Sep 2024](https://www.thedailystar.net/news/bangladesh/education/news/secondary-edn-science-arts-commerce-groups-return-3692371);
[BSS, 3 Jan 2025](https://www.bssnews.net/news/235550);
[NCTB subject structure, effective 2025](https://nctb.portal.gov.bd/site/page/d61acf4b-951c-4a7c-abcd-666870078977)).
NCTB's subject structure lists Physics (পদার্থবিজ্ঞান) for the
science group; the SSC assessment guidance (from 2027) keeps creative (সৃজনশীল) and MCQ
sections. The 2026 Physics book has 13 chapters (chapter list in
`IDS.md` in the nctb-mcp repo, read from the book's contents page).
