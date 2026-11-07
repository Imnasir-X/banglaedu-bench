"""Item schema and validator for BanglaEdu Bench JSONL files.

Dependency-free on purpose. `schema/item.schema.json` documents the shape for
other tools; this module is the source of truth and also enforces cross-field
rules JSON Schema cannot express (numeric keys must carry a recomputable
expression, past-paper items need documented permission, srijonshil items need
exactly the four NCTB parts, every item ships with verified=false until two
human reviewers accept it).
"""

from __future__ import annotations

import re
from typing import Any

from . import CANARY
from .normalize import BN_LABELS

SCHEMA_VERSION = "0.1"

SUBJECTS = {"physics": "পদার্থবিজ্ঞান"}
TASK_TYPES = {"mcq", "short_answer", "srijonshil"}
DIFFICULTIES = {"easy", "medium", "hard"}
# NCTB's four thinking levels (used for srijonshil parts and as the item level).
THINKING_LEVELS = {
    "knowledge": "জ্ঞান",
    "comprehension": "অনুধাবন",
    "application": "প্রয়োগ",
    "higher_ability": "উচ্চতর দক্ষতা",
}
SRIJONSHIL_PARTS = (
    ("ক", "knowledge", 1),
    ("খ", "comprehension", 2),
    ("গ", "application", 3),
    ("ঘ", "higher_ability", 4),
)
SOURCE_TYPES = {
    "original_syllabus_aligned",  # written for this benchmark to the NCTB syllabus
    "licensed_reuse",  # third-party item reused under a licence that allows it
    "textbook_exercise",  # NCTB textbook exercise: needs written NCTB permission
    "board_past_paper",  # education-board past paper: needs written permission
}
NEEDS_PERMISSION = {"licensed_reuse", "textbook_exercise", "board_past_paper"}
CHECK_METHODS = {"python_expression", "author_physics_knowledge", "reference_checked"}
SPLITS = {"dev", "test"}

ID_RE = re.compile(r"^bebench-phy-[0-9]{3}$")
TOPIC_RE = re.compile(r"^nctb:phy:c9-10:(bn|en):ch[0-9]{2}:t[0-9]{2}(:s[0-9]{2})?$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED = (
    "id",
    "version",
    "schema_version",
    "canary",
    "language",
    "class_level",
    "subject",
    "chapter",
    "topic_id",
    "task_type",
    "question",
    "answer_key",
    "marking_rubric",
    "max_marks",
    "explanation",
    "difficulty",
    "thinking_level",
    "source",
    "answer_check",
    "verified",
    "review",
    "split",
)


def _s(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_short_answer_key(key: Any, where: str, errs: list[str]) -> None:
    """A short answer key has reference text and, for calculations, a numeric block."""
    if not isinstance(key, dict):
        errs.append(f"{where}: answer_key must be an object")
        return
    if not _s(key.get("text")):
        errs.append(f"{where}: answer_key.text (reference answer) is required")
    aliases = key.get("aliases", [])
    if not isinstance(aliases, list) or not all(_s(a) for a in aliases):
        errs.append(f"{where}: answer_key.aliases must be a list of strings")
    num = key.get("numeric")
    if num is not None:
        if not isinstance(num, dict) or not _num(num.get("value")):
            errs.append(f"{where}: answer_key.numeric.value must be a number")
            return
        if not isinstance(num.get("unit", ""), str):
            errs.append(f"{where}: answer_key.numeric.unit must be a string")
        for k in ("rel_tol", "abs_tol"):
            t = num.get(k, 0)
            if not _num(t) or t < 0:
                errs.append(f"{where}: answer_key.numeric.{k} must be >= 0")
        if num.get("rel_tol", 0) == 0 and num.get("abs_tol", 0) == 0:
            errs.append(f"{where}: numeric key needs rel_tol or abs_tol > 0")
        alt = num.get("alt_values", [])
        if not isinstance(alt, list) or not all(_num(a) for a in alt):
            errs.append(f"{where}: answer_key.numeric.alt_values must be numbers")


def _check_rubric(rubric: Any, max_marks: Any, where: str, errs: list[str]) -> None:
    if not isinstance(rubric, list) or not rubric:
        errs.append(f"{where}: marking_rubric must be a non-empty list of criteria")
        return
    total = 0
    for i, c in enumerate(rubric):
        if not isinstance(c, dict) or not _s(c.get("criterion")) or not _num(c.get("marks")):
            errs.append(f"{where}: marking_rubric[{i}] needs criterion and marks")
            return
        total += c["marks"]
    if _num(max_marks) and abs(total - max_marks) > 1e-9:
        errs.append(f"{where}: rubric marks sum to {total}, expected max_marks {max_marks}")


def _check_answer_check(chk: Any, has_numeric: bool, where: str, errs: list[str]) -> None:
    if not isinstance(chk, dict) or chk.get("method") not in CHECK_METHODS:
        errs.append(f"{where}: answer_check.method must be one of {sorted(CHECK_METHODS)}")
        return
    if has_numeric and (chk["method"] != "python_expression" or not _s(chk.get("expression"))):
        errs.append(f"{where}: numeric keys need answer_check python_expression + expression")
    if chk["method"] == "reference_checked" and not _s(chk.get("reference")):
        errs.append(f"{where}: reference_checked needs answer_check.reference")


def validate_item(item: Any) -> list[str]:
    """Return a list of human-readable errors; empty means valid."""
    if not isinstance(item, dict):
        return ["item is not a JSON object"]
    iid = item.get("id", "<no id>")
    errs = [f"{iid}: missing field '{k}'" for k in REQUIRED if k not in item]
    if errs:
        return errs

    if not ID_RE.match(str(iid)):
        errs.append(f"{iid}: id must look like bebench-phy-001")
    if not VERSION_RE.match(str(item["version"])):
        errs.append(f"{iid}: version tag must be semver like 0.1.0")
    if item["schema_version"] != SCHEMA_VERSION:
        errs.append(f"{iid}: schema_version must be {SCHEMA_VERSION}")
    if item["canary"] != CANARY:
        errs.append(f"{iid}: canary string missing or altered")
    if item["language"] not in {"bn", "en"}:
        errs.append(f"{iid}: language must be bn or en")
    if item["class_level"] != [9, 10]:
        errs.append(f"{iid}: class_level must be [9, 10] in v0.1")
    if item["subject"] not in SUBJECTS:
        errs.append(f"{iid}: subject must be physics in v0.1")
    ch = item["chapter"]
    if not (isinstance(ch, dict) and isinstance(ch.get("number"), int) and _s(ch.get("title_bn"))):
        errs.append(f"{iid}: chapter needs number and title_bn")
    if not TOPIC_RE.match(str(item["topic_id"])):
        errs.append(
            f"{iid}: topic_id must look like nctb:phy:c9-10:bn:ch02:t07 or ...:ch05:t03:s03"
        )
    elif isinstance(ch, dict) and f":ch{ch.get('number', 0):02d}:" not in item["topic_id"]:
        errs.append(f"{iid}: topic_id chapter does not match chapter.number")
    if not _s(item["question"]):
        errs.append(f"{iid}: empty question")
    if not _s(item["explanation"]):
        errs.append(f"{iid}: empty explanation")
    if item["difficulty"] not in DIFFICULTIES:
        errs.append(f"{iid}: difficulty must be one of {sorted(DIFFICULTIES)}")
    if item["thinking_level"] not in THINKING_LEVELS:
        errs.append(f"{iid}: thinking_level must be one of {sorted(THINKING_LEVELS)}")
    if item["verified"] is not False and item["verified"] is not True:
        errs.append(f"{iid}: verified must be a boolean")
    if item["split"] not in SPLITS:
        errs.append(f"{iid}: split must be dev or test")

    tt = item["task_type"]
    has_numeric = False
    if tt == "mcq":
        opts = item.get("options")
        if not isinstance(opts, list) or len(opts) != 4:
            errs.append(f"{iid}: mcq needs exactly 4 options")
        else:
            labels = tuple(o.get("label") if isinstance(o, dict) else None for o in opts)
            if labels != BN_LABELS:
                errs.append(f"{iid}: option labels must be ক, খ, গ, ঘ in order")
            texts = [o.get("text") for o in opts if isinstance(o, dict)]
            if not all(_s(t) for t in texts) or len(set(texts)) != 4:
                errs.append(f"{iid}: options need 4 distinct non-empty texts")
        key = item["answer_key"]
        if not isinstance(key, dict) or key.get("label") not in BN_LABELS:
            errs.append(f"{iid}: mcq answer_key.label must be one of ক খ গ ঘ")
        if item["max_marks"] != 1:
            errs.append(f"{iid}: mcq max_marks must be 1")
        _check_rubric(item["marking_rubric"], item["max_marks"], iid, errs)
    elif tt == "short_answer":
        check_short_answer_key(item["answer_key"], iid, errs)
        has_numeric = isinstance(item["answer_key"], dict) and "numeric" in item["answer_key"]
        _check_rubric(item["marking_rubric"], item["max_marks"], iid, errs)
    elif tt == "srijonshil":
        parts = item.get("parts")
        if not isinstance(parts, list) or len(parts) != 4:
            errs.append(f"{iid}: srijonshil needs exactly 4 parts (ক খ গ ঘ)")
        else:
            total = 0
            for p, (label, level, marks) in zip(parts, SRIJONSHIL_PARTS, strict=False):
                where = f"{iid}.{label}"
                if not isinstance(p, dict):
                    errs.append(f"{where}: part must be an object")
                    continue
                if p.get("label") != label or p.get("thinking_level") != level:
                    errs.append(f"{where}: part must be label {label} with level {level}")
                if p.get("marks") != marks:
                    errs.append(f"{where}: part {label} must carry {marks} marks")
                if not _s(p.get("question")):
                    errs.append(f"{where}: empty question")
                check_short_answer_key(p.get("answer_key"), where, errs)
                _check_rubric(p.get("marking_rubric"), p.get("marks"), where, errs)
                if isinstance(p.get("answer_key"), dict) and "numeric" in p["answer_key"]:
                    has_numeric = True
                    _check_answer_check(p.get("answer_check"), True, where, errs)
                total += p.get("marks", 0) if _num(p.get("marks")) else 0
            if item["max_marks"] != 10 or total != 10:
                errs.append(f"{iid}: srijonshil max_marks must be 10")
        if not isinstance(item["marking_rubric"], list):
            errs.append(f"{iid}: srijonshil marking_rubric must be a list (may be summary)")
    else:
        errs.append(f"{iid}: task_type must be one of {sorted(TASK_TYPES)}")

    if tt != "srijonshil":
        _check_answer_check(item["answer_check"], has_numeric, iid, errs)

    src = item["source"]
    if not isinstance(src, dict):
        errs.append(f"{iid}: source must be an object")
    else:
        stype = src.get("type")
        if stype not in SOURCE_TYPES:
            errs.append(f"{iid}: source.type must be one of {sorted(SOURCE_TYPES)}")
        for k in ("citation", "author", "license"):
            if not _s(src.get(k)):
                errs.append(f"{iid}: source.{k} is required")
        if not DATE_RE.match(str(src.get("created", ""))):
            errs.append(f"{iid}: source.created must be YYYY-MM-DD")
        if stype in NEEDS_PERMISSION and not _s(src.get("permission")):
            errs.append(f"{iid}: source.type '{stype}' requires source.permission")

    rev = item["review"]
    if not isinstance(rev, dict) or not isinstance(rev.get("reviewers"), list):
        errs.append(f"{iid}: review must be an object with a reviewers list")
    elif item["verified"] is True and len(rev["reviewers"]) < 2:
        errs.append(f"{iid}: verified=true requires two recorded reviewers")
    return errs


def validate_items(items: list[dict]) -> list[str]:
    """Validate a list of items, including uniqueness of ids and question text."""
    errs: list[str] = []
    seen_ids: set = set()
    seen_q: set = set()
    for item in items:
        errs.extend(validate_item(item))
        if not isinstance(item, dict):
            continue
        iid, q = item.get("id"), item.get("question")
        if iid in seen_ids:
            errs.append(f"{iid}: duplicate id")
        if q in seen_q:
            errs.append(f"{iid}: duplicate question text")
        seen_ids.add(iid)
        seen_q.add(q)
    return errs
