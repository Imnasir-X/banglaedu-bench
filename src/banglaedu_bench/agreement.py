"""Inter-rater agreement: percent agreement and Cohen's kappa (unweighted and weighted)."""

from __future__ import annotations

from collections import Counter


def percent_agreement(a: list, b: list) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty rating lists")
    return sum(x == y for x, y in zip(a, b, strict=False)) / len(a)


def cohens_kappa(a: list, b: list, labels: list | None = None, weights: str | None = None) -> float:
    """Cohen's kappa. weights=None (nominal), 'linear' or 'quadratic' (ordinal labels).

    For weighted kappa `labels` must be given in their natural order.
    Returns 1.0 when both raters use a single identical category (perfect, no variance).
    """
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty rating lists")
    cats = labels or sorted(set(a) | set(b), key=str)
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    n = len(a)
    if weights is None:

        def w(i, j):
            return 0.0 if i == j else 1.0
    elif weights == "linear":

        def w(i, j):
            return abs(i - j) / (k - 1) if k > 1 else 0.0
    elif weights == "quadratic":

        def w(i, j):
            return ((i - j) / (k - 1)) ** 2 if k > 1 else 0.0
    else:
        raise ValueError("weights must be None, 'linear' or 'quadratic'")

    obs = Counter((idx[x], idx[y]) for x, y in zip(a, b, strict=False))
    pa = Counter(idx[x] for x in a)
    pb = Counter(idx[y] for y in b)
    observed = sum(w(i, j) * c for (i, j), c in obs.items()) / n
    expected = sum(w(i, j) * pa[i] * pb[j] for i in range(k) for j in range(k)) / (n * n)
    if expected == 0:
        return 1.0 if observed == 0 else 0.0
    return 1.0 - observed / expected


def interpret_kappa(k: float) -> str:
    """Landis & Koch (1977) bands, as commonly reported."""
    if k < 0:
        return "poor"
    for cut, label in ((0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial")):
        if k <= cut:
            return label
    return "almost perfect"
