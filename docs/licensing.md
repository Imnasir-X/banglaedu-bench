# Licensing decisions

Not legal advice. Sources and reasoning are in `docs/research.md` §3.

## Decided in v0.1

| What | Licence | Why |
|---|---|---|
| Code (`src/`, `scripts/`, `tests/`) | **MIT** (`LICENSE`) | Owner's instruction. |
| Item provenance | **Original items only** | NCTB textbooks are Board copyright and "all rights reserved"; board papers and guide books have no open licence. Facts, formulas and syllabus concepts are not ours to license, but our wording is. |
| Textbook content | **Not copied, not mirrored** | Items cite chapter and section ids only. Grounding uses `nctb-data` (structure, titles, objectives, page pointers), not book text. |
| Board past papers, textbook exercises | **Excluded** | Schema refuses them unless `source.permission` records written permission. |

## Needs the owner's decision before release

1. **Dataset licence for the items.** Items are currently tagged
   `CC BY 4.0 (proposed; owner to confirm)`. Options:
   * **CC BY 4.0** (proposed): maximum reuse, including commercial; attribution required.
     Fits a public benchmark and lets the MCP and other tools redistribute it.
   * **CC BY-SA 4.0**: derivatives must stay open.
   * **CC BY-NC 4.0**: blocks commercial use; many labs then cannot run it in products or
     evals, and it is harder to combine with the MIT code.
   Whichever is chosen, set `DATA_LICENSE` in `scripts/build_seed.py`, rebuild, and update
   the card.
2. **Test split terms.** The private test split is not released. Decide whether third
   parties may request evaluation (you run their model) and under what terms.
3. **Reviewer contributions.** Teachers' corrections become part of the items; get their
   agreement to the chosen licence and decide how they are credited.
4. **Topic-id data from `nctb-data`.** Section titles and numbers come from the NCTB book.
   Short titles and numbering are likely fine as factual metadata, but the licence of the
   `nctb-data` layer is owned by the nctb-mcp project; keep the two consistent.
5. **Whether to ever seek NCTB permission** to include official textbook exercises or
   board questions in a later, separately licensed split.
