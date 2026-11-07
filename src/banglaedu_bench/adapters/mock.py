"""Offline mock models: sanity-check the harness and scorers without any API.

mock-oracle    answers every item correctly (harness should report 100%).
mock-random    seeded random guesses (MCQ ~25%).
mock-constant  always answers ক / 0 (option-bias and parser sanity check).
mock-grounded  correct only when curriculum grounding is in the prompt; tests the
               with/without-MCP plumbing, not a real model.
mock-judge     deterministic token-overlap "judge" for tests and calibration demos.
"""

from __future__ import annotations

import hashlib
import random

from ..judge import overlap_score
from ..normalize import BN_LABELS, ascii_to_bn_digits
from .base import Adapter


def _oracle_text(meta: dict) -> str:
    item, part = meta["item"], meta.get("part")
    if item["task_type"] == "mcq":
        return f"উত্তর: {item['answer_key']['label']}"
    key = (part or item)["answer_key"]
    if "numeric" in key:
        num = key["numeric"]
        return f"{key['text']}\nউত্তর: {num['value']} {num.get('unit', '')}".strip()
    return f"উত্তর: {key['text']}"


class MockOracle(Adapter):
    name = "mock-oracle"

    def generate(self, messages, meta=None):
        return _oracle_text(meta or {})


class MockRandom(Adapter):
    name = "mock-random"

    def __init__(self, seed: int = 0, **_):
        self.seed = seed

    def generate(self, messages, meta=None):
        meta = meta or {}
        tag = (
            f"{self.seed}:{meta.get('item', {}).get('id')}:{(meta.get('part') or {}).get('label')}"
        )
        rng = random.Random(int(hashlib.sha256(tag.encode()).hexdigest()[:8], 16))
        if meta.get("item", {}).get("task_type") == "mcq":
            return f"উত্তর: {rng.choice(BN_LABELS)}"
        return f"উত্তর: {ascii_to_bn_digits(str(rng.randint(1, 500)))}"


class MockConstant(Adapter):
    name = "mock-constant"

    def generate(self, messages, meta=None):
        if (meta or {}).get("item", {}).get("task_type") == "mcq":
            return "উত্তর: ক"
        return "উত্তর: ০"


class MockGrounded(Adapter):
    """Correct iff the prompt carries grounding context; otherwise behaves like ক/0."""

    name = "mock-grounded"

    def generate(self, messages, meta=None):
        meta = meta or {}
        if meta.get("grounding"):
            return _oracle_text(meta)
        return MockConstant().generate(messages, meta)


class MockJudge(Adapter):
    name = "mock-judge"

    def generate(self, messages, meta=None):
        meta = meta or {}
        s = overlap_score(meta.get("reference", ""), meta.get("answer", ""), meta["max_marks"])
        return f'{{"score": {int(s)}, "reason": "token overlap (mock)"}}'


MOCKS = {
    "mock-oracle": MockOracle,
    "mock-random": MockRandom,
    "mock-constant": MockConstant,
    "mock-grounded": MockGrounded,
    "mock-judge": MockJudge,
}
