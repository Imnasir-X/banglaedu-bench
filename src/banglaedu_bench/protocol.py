"""Locked run protocol. A score is comparable only when this file was followed.

Temperature 0 and 1024 completion tokens are the spec. A run may override them
for a debug, and the card then says the result is not comparable. API errors
are not wrong answers. The judge is a different model from the one under test.
"""

from __future__ import annotations

import random
import urllib.parse

from .curriculum import BAND_ORDER, class_band
from .prompts import PROMPT_FINGERPRINT, PROMPT_VERSION

TEMPERATURE = 0.0
MAX_TOKENS = 1024
# Bangladesh board grade F is below 33 percent. Used only after a band is checked.
PASS_PCT = 33.0
_LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}


def left_the_machine(model) -> bool:
    """True when the prompt was sent to a host that is not this computer."""
    url = getattr(model, "base_url", "") or ""
    if not url:
        return False
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host not in _LOCAL_HOSTS


def protocol_deviation(model) -> bool:
    """True when the adapter sampled differently from the locked spec.

    Mocks have no sampling settings. Missing attributes follow the spec.
    """
    temperature = getattr(model, "temperature", None)
    max_tokens = getattr(model, "max_tokens", None)
    temperature_off = temperature is not None and float(temperature) != TEMPERATURE
    tokens_off = max_tokens is not None and int(max_tokens) != MAX_TOKENS
    return temperature_off or tokens_off


def same_model(model, judge) -> bool:
    """The judge must not be the model being measured."""
    if judge is None:
        return False
    return getattr(model, "name", None) == getattr(judge, "name", None)


def bootstrap_ci(preds: list[dict], *, rounds: int = 1000, seed: int = 0) -> list[float] | None:
    """95% interval for the marks-weighted percent, by resampling items.

    Infrastructure errors and answers that still need a judge are left out,
    matching the headline score. Fewer than two scored items has no interval.
    """
    pairs = []
    for pred in preds:
        if pred.get("method") in {"needs_judge", "error"}:
            continue
        maximum = pred.get("max_marks") or 0
        if maximum <= 0:
            continue
        pairs.append((float(pred["score"]), float(maximum)))
    if len(pairs) < 2:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(rounds):
        draw = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        total = sum(maximum for _, maximum in draw)
        means.append(100 * sum(score for score, _ in draw) / total)
    means.sort()
    low = means[int(0.025 * (rounds - 1))]
    high = means[int(0.975 * (rounds - 1))]
    return [round(low, 2), round(high, 2)]


def canary_echoes(preds: list[dict]) -> int:
    """How many replies contain the benchmark canary.

    A public dev set can leak into training. A reply that repeats the canary
    is contamination, and that run is not a comparable score.
    """
    from banglaedu_bench import CANARY_GUID

    n = 0
    for pred in preds:
        blobs = [str(pred.get("output") or "")]
        for part in pred.get("parts") or []:
            if isinstance(part, dict):
                blobs.append(str(part.get("output") or ""))
        if any(CANARY_GUID in blob for blob in blobs):
            n += 1
    return n


def threshold_block(items: list[dict], preds: list[dict], model, by_band: dict) -> dict:
    """What a published pass would require. The physics seed does not meet it."""
    n_verified = sum(1 for item in items if item.get("verified") is True)
    reasons = []
    if n_verified < len(items):
        reasons.append("items are not yet two-reviewer verified")
    if protocol_deviation(model):
        reasons.append("sampling left temperature 0 and 1024 tokens")
    if left_the_machine(model):
        reasons.append("prompts left this machine; treat the split as exposed")
    echoes = canary_echoes(preds)
    if echoes:
        reasons.append(f"{echoes} replies echoed the canary; treat the run as contaminated")
    grouped: dict[str, list] = {name: [] for name in BAND_ORDER}
    for item in items:
        band = class_band(item.get("class_level")) if isinstance(item, dict) else None
        if band in grouped:
            grouped[band].append(item)
    bands = {}
    for name in BAND_ORDER:
        bucket = by_band.get(name) or {}
        group = grouped[name]
        checked = bool(group) and all(item.get("verified") is True for item in group)
        pct = bucket.get("pct")
        passed = None
        if checked and pct is not None:
            passed = pct >= PASS_PCT
        bands[name] = {
            "pct": pct,
            "n": bucket.get("n", 0),
            "pass": passed,
            "pass_pct": PASS_PCT if checked else None,
        }
    if n_verified < len(items):
        status = "unverified_seed"
    elif reasons:
        status = "not_comparable"
    else:
        status = "checked"
    return {
        "status": status,
        "comparable": not reasons,
        "rule": (
            "Report primary (class 5), junior (6–8), SSC (9–10) and college HSC (11–12) "
            "separately, and inside each band by stream and subject. One average is not a pass. "
            "The pass line is 33 percent of scored marks, and it is filled in only for a band "
            "whose every item in the run is verified. Otherwise pass is empty."
        ),
        "reasons": reasons,
        "by_band": bands,
        "overall_pct_ci95": bootstrap_ci(preds),
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_FINGERPRINT,
    }


def protocol_card(model, judge) -> dict:
    return {
        "temperature_spec": TEMPERATURE,
        "max_tokens_spec": MAX_TOKENS,
        "adapter_temperature": getattr(model, "temperature", None),
        "adapter_max_tokens": getattr(model, "max_tokens", None),
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_FINGERPRINT,
        "judge": judge.name if judge else None,
        "endpoint": getattr(model, "base_url", None),
        "left_the_machine": left_the_machine(model),
        "deviation": protocol_deviation(model),
    }
