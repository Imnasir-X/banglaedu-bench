"""Pluggable LLM judge for written answers, scored against the item's marking rubric.

Any adapter can be the judge. Use a different model family from the one being
evaluated, temperature 0, and report the calibration result (calibration.py)
next to every judged score: an uncalibrated judge is not a gold label.
"""

from __future__ import annotations

import json
import re

from .adapters.base import Adapter
from .normalize import normalize_text

JUDGE_PROMPT_VERSION = "judge-v0.1"

JUDGE_SYSTEM = (
    "You are a strict, fair SSC (Class 9-10) physics examiner in Bangladesh. "
    "You grade a student's written answer in Bangla against a reference answer and a "
    "marking rubric. Award only marks the rubric allows. Do not reward length, style or "
    "English vs Bangla wording; reward correct physics and the rubric criteria. "
    'Reply with JSON only: {"score": <number>, "reason": "<one short sentence>"}.'
)


def build_judge_messages(
    question: str, reference: str, rubric: list[dict], max_marks: float, answer: str
) -> list[dict]:
    rubric_lines = "\n".join(f"- ({c['marks']} marks) {c['criterion']}" for c in rubric)
    user = (
        f"Question:\n{question}\n\n"
        f"Reference answer:\n{reference}\n\n"
        f"Marking rubric (maximum {max_marks} marks):\n{rubric_lines}\n\n"
        f"Student answer:\n{answer}\n\n"
        f"Give an integer score from 0 to {int(max_marks)}."
    )
    return [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}]


def parse_judge_score(text: str, max_marks: float) -> float | None:
    if not text:
        return None
    for m in re.finditer(r"\{.*?\}", text, re.DOTALL):
        try:
            obj = json.loads(m.group(0))
            if "score" in obj:
                return max(0.0, min(float(obj["score"]), float(max_marks)))
        except (ValueError, TypeError):
            continue
    m = re.search(r"score\D{0,5}(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        return max(0.0, min(float(m.group(1)), float(max_marks)))
    return None


class Judge:
    """Wraps an adapter and grades one answer."""

    def __init__(self, adapter: Adapter):
        self.adapter = adapter

    @property
    def name(self) -> str:
        return self.adapter.name

    def grade(
        self, question: str, reference: str, rubric: list[dict], max_marks: float, answer: str
    ) -> tuple[float | None, str]:
        msgs = build_judge_messages(question, reference, rubric, max_marks, answer)
        raw = self.adapter.generate(
            msgs,
            meta={
                "role": "judge",
                "reference": reference,
                "answer": answer,
                "max_marks": max_marks,
            },
        )
        return parse_judge_score(raw, max_marks), raw


def overlap_score(reference: str, answer: str, max_marks: float) -> float:
    """Deterministic token-overlap grade used by the mock judge (tests/offline demos only)."""
    ref = set(normalize_text(reference).split())
    ans = set(normalize_text(answer).split())
    if not ref or not ans:
        return 0.0
    recall = len(ref & ans) / len(ref)
    return float(round(recall * max_marks))
