"""Answer extraction and scoring.

* MCQ: robust option parsing across ক/খ/গ/ঘ, A/B/C/D, 1-4 and ১-৪, then exact match.
* Numeric: number extraction with Bangla digits, Indian digit grouping, ×10^n and
  superscript exponents, fractions; compared with relative/absolute tolerance.
* Text short answers: normalised exact/alias match ("contains" for one-term keys);
  anything richer goes to the pluggable LLM judge (see judge.py).
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import asdict, dataclass

from .normalize import (
    BN_LABELS,
    bn_to_ascii_digits,
    label_index,
    normalize_text,
)

_BN_CHAR = r"\u0980-\u09FF"
_LABEL = r"[কখগঘ]|[A-Da-d]|[1-4]|[১-৪]"
_MARKER = r"(?:সঠিক\s*উত্তর|উত্তর|correct\s*answer|correct\s*option|final\s*answer|answer|ans)"
_MARKER_RE = re.compile(
    _MARKER
    + r"\s*(?:হলো|হল|হচ্ছে|is|:|：|-|–|=)?\s*(?:হলো|হল|is|:)?\s*[\(\[]?\s*("
    + _LABEL
    + r")\s*[\)\]]?(?!["
    + _BN_CHAR
    + r"A-Za-z0-9])",
    re.IGNORECASE,
)
# A standalone label: not glued to other Bangla letters/vowel signs or Latin letters.
_STANDALONE_BN = re.compile(r"(?<![" + _BN_CHAR + r"])([কখগঘ])(?![" + _BN_CHAR + r"])")
_STANDALONE_EN = re.compile(r"(?:(?<=\()|(?<![A-Za-z0-9]))([A-D])(?=[\)\.:।]|\s*$)")
_ANSWER_MARKER_RE = re.compile(_MARKER, re.IGNORECASE)


@dataclass
class Score:
    score: float
    max_marks: float
    method: str  # exact | numeric | text | judge | unparsed | error
    parsed: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _after_last_marker(text: str) -> str | None:
    matches = list(_ANSWER_MARKER_RE.finditer(text))
    return text[matches[-1].end() :] if matches else None


def parse_mcq(text: str, options: list[dict] | None = None) -> str | None:
    """Return the chosen Bangla label (ক/খ/গ/ঘ) or None if it cannot be determined."""
    if not text:
        return None
    text = unicodedata.normalize("NFC", text)

    # 1. Explicit "উত্তর: খ" / "Answer: B" markers; the last one wins.
    marked = _MARKER_RE.findall(text)
    if marked:
        idx = label_index(marked[-1])
        if idx is not None:
            return BN_LABELS[idx]

    def standalone(chunk: str) -> set[int]:
        found = {BN_LABELS.index(m) for m in _STANDALONE_BN.findall(chunk)}
        found |= {ord(m) - ord("A") for m in _STANDALONE_EN.findall(chunk)}
        stripped = bn_to_ascii_digits(chunk.strip().strip("().।:"))
        if stripped in {"1", "2", "3", "4"}:
            found.add(int(stripped) - 1)
        return found

    # 2. A single standalone label on the last non-empty line, then in the whole text.
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for chunk in ([lines[-1]] if lines else []) + [text]:
        found = standalone(chunk)
        if len(found) == 1:
            return BN_LABELS[found.pop()]

    # 3. Exactly one option's text appears in the answer.
    if options:
        norm = normalize_text(text)
        hits = [
            o["label"]
            for o in options
            if normalize_text(o["text"]) and normalize_text(o["text"]) in norm
        ]
        # Drop options whose text is a substring of another hit (e.g. "৬" inside "৬০").
        if len(hits) > 1:
            texts = {o["label"]: normalize_text(o["text"]) for o in options}
            hits = [h for h in hits if not any(h != o and texts[h] in texts[o] for o in hits)]
        if len(hits) == 1:
            return hits[0]
    return None


def score_mcq(text: str, item: dict) -> Score:
    parsed = parse_mcq(text, item.get("options"))
    if parsed is None:
        return Score(0, 1, "unparsed")
    correct = parsed == item["answer_key"]["label"]
    return Score(1 if correct else 0, 1, "exact", parsed)


# ---------------------------------------------------------------- numeric
_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SUP_RUN = re.compile(r"([⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)")
_NUM_RE = re.compile(
    r"(?<![A-Za-z0-9.^+\-−])"
    r"([-+−]?\d+(?:\.\d+)?|[-+−]?\.\d+)"
    r"(?:\s*/\s*(\d+(?:\.\d+)?))?"  # fraction a/b
    r"(?:\s*(?:×|x|X|\*|·)\s*10\s*\^?\s*\(?\s*([-+−]?\d+)\s*\)?|[eE]([-+−]?\d+))?"
)
_GROUPING = re.compile(r"(?<=\d),(?=\d{2,3}(?:\D|$))")


def _prep_numbers(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = bn_to_ascii_digits(text)
    text = _SUP_RUN.sub(lambda m: "^" + m.group(1).translate(_SUPERSCRIPT), text)
    # Repeat to collapse Indian grouping like 4,20,000.
    for _ in range(3):
        text = _GROUPING.sub("", text)
    return text.replace("−", "-")


def extract_numbers(text: str) -> list[float]:
    """All numbers in reading order, with ×10^n / e-notation / a/b applied."""
    out: list[float] = []
    for m in _NUM_RE.finditer(_prep_numbers(text)):
        base, denom, exp10, exp_e = m.groups()
        try:
            val = float(base.replace("−", "-"))
            if denom:
                d = float(denom)
                if d == 0:
                    continue
                val /= d
            exp = exp10 or exp_e
            if exp:
                val *= 10 ** int(exp.replace("−", "-"))
        except (ValueError, OverflowError):
            continue
        out.append(val)
    return out


def parse_numeric(text: str) -> float | None:
    """The answer number: first number after the last 'উত্তর/answer' marker, else the last."""
    if not text:
        return None
    tail = _after_last_marker(text)
    if tail is not None:
        nums = extract_numbers(tail)
        if nums:
            return nums[0]
    nums = extract_numbers(text)
    return nums[-1] if nums else None


def numeric_match(value: float, key: dict) -> bool:
    targets = [key["value"], *key.get("alt_values", [])]
    rel, abs_ = key.get("rel_tol", 0.0), key.get("abs_tol", 0.0)
    return any(math.isclose(value, t, rel_tol=rel, abs_tol=abs_) for t in targets)


def score_numeric(text: str, key: dict, max_marks: float) -> Score:
    val = parse_numeric(text)
    if val is None:
        return Score(0, max_marks, "unparsed")
    ok = numeric_match(val, key["numeric"])
    return Score(max_marks if ok else 0, max_marks, "numeric", repr(val))


# ---------------------------------------------------------------- text
def text_match(text: str, key: dict) -> bool:
    """Normalised match of the answer against the reference and its aliases.

    Short reference terms (up to three words) match if they appear in the
    answer; longer references must match exactly. Longer, explanatory answers
    should be scored by the LLM judge instead.
    """
    region = _after_last_marker(text) or text
    ans = normalize_text(region)
    if not ans:
        return False
    for ref in [key["text"], *key.get("aliases", [])]:
        r = normalize_text(ref)
        if not r:
            continue
        if ans == r or (len(r.split()) <= 3 and r in ans):
            return True
    return False


def score_text(text: str, key: dict, max_marks: float) -> Score:
    if not text or not text.strip():
        return Score(0, max_marks, "unparsed")
    ok = text_match(text, key)
    return Score(max_marks if ok else 0, max_marks, "text")
