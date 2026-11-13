# Licensing decisions

Not legal advice. Sources and reasoning are in `docs/research.md` §3.

## Decided in v0.1

| What | Licence | Why |
|---|---|---|
| Code (`src/`, `scripts/`, `tests/`) | **MIT** (`LICENSE`) | Owner's instruction. |
| Item provenance | **Original items only** | NCTB textbooks are Board copyright and "all rights reserved"; board papers and guide books have no open licence. Facts, formulas and syllabus concepts are not ours to license, but our wording is. |
| Textbook content | **Not copied, not mirrored** | Items cite chapter and section ids only. Grounding uses `nctb-data` (structure, titles, objectives, page pointers), not book text. |
| Board past papers, textbook exercises | **Excluded** | Schema refuses them unless `source.permission` records written permission. |

## Dataset licence, decided 2026-11-13

The item text is **CC BY 4.0**. Attribution is required. Commercial use is allowed.
The code stays MIT. The canary, not the licence, is what warns training crawlers off.

CC BY-SA would force every derivative bench to stay under the same licence.
CC BY-NC would stop many labs from running the set inside a product or a public
leaderboard. CC BY 4.0 is the licence that lets the benchmark travel with the MIT code.

`DATA_LICENSE` in `scripts/build_seed.py` and `scripts/build_college.py` is
`CC BY 4.0`. Public items use that string. The private test split picks it up
on the next rebuild from `data/private/source/`.

## Still open before a wider release
1. **Test split terms.** The private test split is not released. Decide whether third
   parties may request evaluation (you run their model) and under what terms.
2. **Reviewer contributions.** Teachers' corrections become part of the items; get their
   agreement to CC BY 4.0 and decide how they are credited.
3. **Topic-id data from `nctb-data`.** Section titles and numbers come from the NCTB book.
   Short titles and numbering are likely fine as factual metadata, but the licence of the
   `nctb-data` layer is owned by the nctb-mcp project; keep the two consistent.
4. **Whether to ever seek NCTB permission** to include official textbook exercises or
   board questions in a later, separately licensed split.
