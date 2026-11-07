"""Recompute every calculation-based answer key from its stored Python expression.

Each numeric key (and each calculation MCQ) stores `answer_check.expression`, a
plain arithmetic expression written from the physics (e.g. "0.5*9.8*3**2").
This module evaluates it in a restricted namespace and checks that the stored
key (or the keyed MCQ option, and no other option) matches. It proves the
arithmetic, not the physics: the physics is what the human reviewers check.
"""

from __future__ import annotations

import ast
import math

from .scoring import extract_numbers

_ALLOWED_FUNCS = {"sqrt": math.sqrt, "pi": math.pi, "log10": math.log10, "log": math.log}
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load, ast.Call,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.FloorDiv, ast.Mod,
)  # fmt: skip


def safe_eval(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"disallowed syntax in expression: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in _ALLOWED_FUNCS:
            raise ValueError(f"unknown name '{node.id}' in expression")
    return float(eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, _ALLOWED_FUNCS))


def _check_numeric(where: str, key: dict, chk: dict, errs: list[str]) -> None:
    got = safe_eval(chk["expression"])
    want = key["numeric"]["value"]
    if not math.isclose(got, want, rel_tol=1e-6, abs_tol=1e-12):
        errs.append(f"{where}: expression gives {got}, key says {want}")


def check_item(item: dict) -> list[str]:
    errs: list[str] = []
    iid = item["id"]
    try:
        if item["task_type"] == "short_answer" and "numeric" in item["answer_key"]:
            _check_numeric(iid, item["answer_key"], item["answer_check"], errs)
        elif item["task_type"] == "srijonshil":
            for p in item["parts"]:
                if "numeric" in p["answer_key"]:
                    _check_numeric(f"{iid}.{p['label']}", p["answer_key"], p["answer_check"], errs)
        elif item["task_type"] == "mcq" and item["answer_check"].get("expression"):
            got = safe_eval(item["answer_check"]["expression"])
            tol = item["answer_check"].get("option_rel_tol", 0.01)

            def matches(text: str) -> bool:
                return any(math.isclose(v, got, rel_tol=tol) for v in extract_numbers(text))

            label = item["answer_key"]["label"]
            hits = [o["label"] for o in item["options"] if matches(o["text"])]
            if hits != [label]:
                errs.append(f"{iid}: expression {got} matches options {hits}, key is {label}")
    except (ValueError, SyntaxError, ZeroDivisionError, KeyError) as exc:
        errs.append(f"{iid}: cannot verify: {exc}")
    return errs


def check_items(items: list[dict]) -> tuple[int, list[str]]:
    """Return (number of items with a recomputed key, errors)."""
    n = 0
    errs: list[str] = []
    for it in items:
        has = (
            (it["task_type"] == "short_answer" and "numeric" in it["answer_key"])
            or (it["task_type"] == "mcq" and it["answer_check"].get("expression"))
            or (
                it["task_type"] == "srijonshil"
                and any("numeric" in p["answer_key"] for p in it["parts"])
            )
        )
        n += bool(has)
        errs += check_item(it)
    return n, errs
