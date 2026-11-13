"""NCTB subject catalog for class 5 through college (class 11–12).

The public question file is still the Class 9–10 physics seed. This module is
the list of subjects the harness will score once items exist. Streams use the
names the project asked for: science, commerce (board name: business studies),
and arts (board name: humanities).

SSC and HSC group membership follows the board subject structure checked on
3 October 2026 (compulsory, compulsory-or-optional, and fourth-subject lists).
Class 5 and class 6–8 follow the NCTB books those years actually sit: Bangla,
English, mathematics, science, Bangladesh and Global Studies, religion, and the
junior practical subjects. College subjects of two papers require paper 1 in
class 11 and paper 2 in class 12.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

BANDS: dict[str, tuple[int, ...]] = {
    "primary": (5,),
    "junior": (6, 7, 8),
    "ssc": (9, 10),
    "hsc": (11, 12),
}
BAND_ORDER = ("primary", "junior", "ssc", "hsc")
BAND_ID = {"primary": "c5", "junior": "c6-8", "ssc": "c9-10", "hsc": "c11-12"}

STREAMS = {
    "common": "সকল বিভাগ",
    "science": "বিজ্ঞান",
    "commerce": "ব্যবসায় শিক্ষা",
    "arts": "মানবিক",
}
STREAM_ORDER = ("common", "science", "commerce", "arts")

# Tasks a band may use. Class 5 has no সৃজনশীল paper. From class 6 up, the
# creative four-part question is the board shape, including HSC.
BAND_TASKS = {
    "primary": frozenset({"mcq", "short_answer"}),
    "junior": frozenset({"mcq", "short_answer", "srijonshil"}),
    "ssc": frozenset({"mcq", "short_answer", "srijonshil"}),
    "hsc": frozenset({"mcq", "short_answer", "srijonshil"}),
}


@dataclass(frozen=True)
class Offer:
    """Classes in which a stream may sit this subject."""

    classes: tuple[int, ...]
    streams: tuple[str, ...]


@dataclass(frozen=True)
class Subject:
    key: str
    name_bn: str
    name_en: str
    topic_code: str
    offers: tuple[Offer, ...]
    # 2: class 11 is paper 1 and class 12 is paper 2. 1: a single college paper.
    hsc_papers: int = 1


def _o(classes: tuple[int, ...], *streams: str) -> Offer:
    return Offer(classes, streams)


def _s(
    key: str,
    name_bn: str,
    name_en: str,
    topic_code: str,
    offers: tuple[Offer, ...],
    hsc_papers: int = 1,
) -> Subject:
    return Subject(key, name_bn, name_en, topic_code, offers, hsc_papers)


# Class spans reused below. An offer may cover more than one band; an item
# must still sit inside a single band.
_C5 = (5,)
_JUN = (6, 7, 8)
_SSC = (9, 10)
_HSC = (11, 12)
_SCHOOL = (5, 6, 7, 8, 9, 10)
_JUN_SSC = (6, 7, 8, 9, 10)
_SSC_HSC = (9, 10, 11, 12)
_ALL = (5, 6, 7, 8, 9, 10, 11, 12)
_FROM6 = (6, 7, 8, 9, 10, 11, 12)

SUBJECTS: dict[str, Subject] = {
    s.key: s
    for s in (
        # --- everyone, including college ---
        _s("bangla", "বাংলা", "Bangla", "bn", (_o(_ALL, "common"),), 2),
        _s("english", "ইংরেজি", "English", "en", (_o(_ALL, "common"),), 2),
        _s("mathematics", "গণিত", "Mathematics", "math", (_o(_SCHOOL, "common"),)),
        _s(
            "ict",
            "তথ্য ও যোগাযোগ প্রযুক্তি",
            "Information and Communication Technology",
            "ict",
            (_o(_FROM6, "common"),),
            1,
        ),
        # --- primary and junior science, then SSC general science ---
        _s(
            "elementary_science",
            "প্রাথমিক বিজ্ঞান",
            "Elementary Science",
            "esci",
            (_o(_C5, "common"),),
        ),
        _s(
            "general_science",
            "বিজ্ঞান",
            "General Science",
            "gsci",
            (_o(_JUN, "common"), _o(_SSC, "arts", "commerce")),
        ),
        _s(
            "bangladesh_and_global_studies",
            "বাংলাদেশ ও বিশ্বপরিচয়",
            "Bangladesh and Global Studies",
            "bgs",
            (_o((5, 6, 7, 8), "common"), _o(_SSC, "science")),
        ),
        # --- religion. College Islam is an arts elective; the others stop at SSC. ---
        _s(
            "islam",
            "ইসলাম শিক্ষা",
            "Islamic Studies",
            "islam",
            (_o(_SCHOOL, "common"), _o(_HSC, "arts")),
            2,
        ),
        _s(
            "hindu_religion",
            "হিন্দুধর্ম শিক্ষা",
            "Hindu Religion Studies",
            "hindu",
            (_o(_SCHOOL, "common"),),
        ),
        _s(
            "buddhist_religion",
            "বৌদ্ধধর্ম শিক্ষা",
            "Buddhist Religion Studies",
            "buddhist",
            (_o(_SCHOOL, "common"),),
        ),
        _s(
            "christian_religion",
            "খ্রিষ্টধর্ম শিক্ষা",
            "Christian Religion Studies",
            "christian",
            (_o(_SCHOOL, "common"),),
        ),
        # --- subjects any group may take, mostly as the fourth subject ---
        _s(
            "physical_education",
            "শারীরিক শিক্ষা, স্বাস্থ্যবিজ্ঞান ও খেলাধুলা",
            "Physical Education, Health Science and Sports",
            "physed",
            (_o(_JUN_SSC, "common"),),
        ),
        _s(
            "career_education",
            "ক্যারিয়ার শিক্ষা",
            "Career Education",
            "career",
            (_o(_SSC, "common"),),
        ),
        _s("agriculture", "কৃষিশিক্ষা", "Agriculture Studies", "agri", (_o(_JUN_SSC, "common"),)),
        _s("home_science", "গার্হস্থ্যবিজ্ঞান", "Home Science", "home", (_o(_JUN_SSC, "common"),)),
        _s("fine_arts", "চারু ও কারুকলা", "Fine Arts", "craft", (_o(_JUN_SSC, "common"),)),
        _s("arabic", "আরবি", "Arabic", "arabic", (_o(_SSC, "common"),)),
        # --- science. College papers are first-class, not an alias of SSC. ---
        _s(
            "physics",
            "পদার্থবিজ্ঞান",
            "Physics",
            "phy",
            (_o(_SSC_HSC, "science"),),
            2,
        ),
        _s("chemistry", "রসায়ন", "Chemistry", "chem", (_o(_SSC_HSC, "science"),), 2),
        _s("biology", "জীববিজ্ঞান", "Biology", "bio", (_o(_SSC_HSC, "science"),), 2),
        _s(
            "higher_mathematics",
            "উচ্চতর গণিত",
            "Higher Mathematics",
            "hmath",
            (_o(_SSC_HSC, "science"),),
            2,
        ),
        # --- arts (humanities), with the college subjects that SSC does not have ---
        _s(
            "history",
            "ইতিহাস",
            "History",
            "hist",
            (_o(_SSC_HSC, "arts"),),
            2,
        ),
        _s(
            "geography",
            "ভূগোল ও পরিবেশ",
            "Geography and Environment",
            "geo",
            (_o(_SSC, "arts"), _o(_HSC, "science", "arts", "commerce")),
            2,
        ),
        _s(
            "civics",
            "পৌরনীতি ও নাগরিকতা",
            "Civics and Citizenship",
            "civics",
            (_o(_SSC, "arts"),),
        ),
        _s(
            "civics_good_governance",
            "পৌরনীতি ও সুশাসন",
            "Civics and Good Governance",
            "civgov",
            (_o(_HSC, "arts"),),
            2,
        ),
        _s(
            "economics",
            "অর্থনীতি",
            "Economics",
            "econ",
            (_o(_SSC, "arts"), _o(_HSC, "arts", "commerce")),
            2,
        ),
        _s(
            "islamic_history",
            "ইসলামের ইতিহাস ও সংস্কৃতি",
            "Islamic History and Culture",
            "ishist",
            (_o(_HSC, "arts"),),
            2,
        ),
        _s("sociology", "সমাজবিজ্ঞান", "Sociology", "socio", (_o(_HSC, "arts"),), 2),
        _s("social_work", "সমাজকর্ম", "Social Work", "socwork", (_o(_HSC, "arts"),), 2),
        _s("logic", "যুক্তিবিদ্যা", "Logic", "logic", (_o(_HSC, "arts"),), 2),
        _s("psychology", "মনোবিজ্ঞান", "Psychology", "psych", (_o(_HSC, "arts"),), 2),
        # --- commerce (business studies). HSC replaces the SSC trio with its own. ---
        _s(
            "accounting",
            "হিসাববিজ্ঞান",
            "Accounting",
            "acct",
            (_o(_SSC_HSC, "commerce"),),
            2,
        ),
        _s(
            "finance_and_banking",
            "ফিন্যান্স ও ব্যাংকিং",
            "Finance and Banking",
            "finbank",
            (_o(_SSC, "commerce"),),
        ),
        _s(
            "business_entrepreneurship",
            "ব্যবসায় উদ্যোগ",
            "Business Entrepreneurship",
            "bizent",
            (_o(_SSC, "commerce"),),
        ),
        _s(
            "business_organization",
            "ব্যবসায় সংগঠন ও ব্যবস্থাপনা",
            "Business Organization and Management",
            "bizorg",
            (_o(_HSC, "commerce"),),
            2,
        ),
        _s(
            "finance_banking_insurance",
            "ফিন্যান্স, ব্যাংকিং ও বীমা",
            "Finance, Banking and Insurance",
            "finins",
            (_o(_HSC, "commerce"),),
            2,
        ),
        _s(
            "production_marketing",
            "উৎপাদন ব্যবস্থাপনা ও বিপণন",
            "Production Management and Marketing",
            "prodmkt",
            (_o(_HSC, "commerce"),),
            2,
        ),
    )
}


def class_band(classes: object) -> str | None:
    """Return the one band that contains every class, or None."""
    if not isinstance(classes, list) or not classes:
        return None
    if not all(isinstance(c, int) and not isinstance(c, bool) for c in classes):
        return None
    hits = [name for name, nums in BANDS.items() if all(c in nums for c in classes)]
    if len(hits) != 1:
        return None
    return hits[0]


def infer_stream(subject: Subject, classes: list[int]) -> str | None:
    """The stream, when exactly one stream can sit these classes."""
    found: list[str] = []
    for offer in subject.offers:
        if all(c in offer.classes for c in classes):
            for stream in offer.streams:
                if stream not in found:
                    found.append(stream)
    if len(found) == 1:
        return found[0]
    return None


def offer_matches(subject: Subject, classes: list[int], stream: str) -> bool:
    return any(
        all(c in offer.classes for c in classes) and stream in offer.streams
        for offer in subject.offers
    )


def resolve_stream(item: dict) -> str:
    """Declared stream, or the only stream the catalog allows for this item."""
    if item.get("stream"):
        return str(item["stream"])
    subject = SUBJECTS[item["subject"]]
    inferred = infer_stream(subject, item["class_level"])
    if inferred is None:
        raise ValueError(f"{item.get('id')}: stream is required for this subject and class")
    return inferred


def paper_error(subject: Subject, classes: list[int], paper: object) -> str | None:
    """None when the paper field is legal for this subject and class."""
    if paper is not None and paper not in (1, 2):
        return "paper must be 1 or 2"
    if not (set(classes) & {11, 12}):
        return None
    if subject.hsc_papers != 2:
        return None
    if classes == [11] and paper == 1:
        return None
    if classes == [12] and paper == 2:
        return None
    return (
        "a college subject of two papers needs class_level [11] with paper 1, "
        "or class_level [12] with paper 2 (class 11 is the first paper, class 12 the second)"
    )


def describe(item: dict) -> dict:
    """Band, subject and stream for prompts, scoring and the run card."""
    classes = item["class_level"]
    band = class_band(classes)
    if band is None:
        raise ValueError(f"{item.get('id')}: class_level is not inside one band from 5 to 12")
    subject = SUBJECTS.get(item["subject"])
    if subject is None:
        raise ValueError(f"{item.get('id')}: unknown subject {item.get('subject')!r}")
    stream = resolve_stream(item)
    return {
        "class_band": band,
        "class_level": list(classes),
        "subject": subject.key,
        "subject_bn": subject.name_bn,
        "subject_en": subject.name_en,
        "stream": stream,
        "stream_bn": STREAMS[stream],
        "paper": item.get("paper"),
    }


def exam_label(info: dict) -> str:
    paper = f", paper {info['paper']}" if info.get("paper") else ""
    return (
        f"{info['class_band']} {info['subject_en']} ({info['subject_bn']}), {info['stream']}{paper}"
    )


def id_ok(subject: Subject, band: str, item_id: str) -> bool:
    span = BAND_ID[band]
    return (
        re.fullmatch(rf"bebench-{re.escape(subject.topic_code)}-{span}-[0-9]{{3}}", item_id)
        is not None
    )


def topic_ok(subject: Subject, band: str, topic_id: str, chapter: int, language: str) -> bool:
    span = BAND_ID[band]
    pattern = (
        rf"nctb:{re.escape(subject.topic_code)}:{span}:{language}:"
        rf"ch{chapter:02d}:t[0-9]{{2}}(:s[0-9]{{2}})?"
    )
    return re.fullmatch(pattern, topic_id) is not None


def catalog_slots() -> list[dict]:
    """One row per subject, band and stream the catalog allows."""
    seen: set[tuple] = set()
    rows: list[dict] = []
    for subject in SUBJECTS.values():
        for offer in subject.offers:
            by_band: dict[str, list[int]] = {}
            for number in offer.classes:
                band = class_band([number])
                assert band is not None
                by_band.setdefault(band, []).append(number)
            for band in BAND_ORDER:
                if band not in by_band:
                    continue
                for stream in offer.streams:
                    key = (subject.key, band, stream)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "subject": subject.key,
                            "name_bn": subject.name_bn,
                            "name_en": subject.name_en,
                            "class_band": band,
                            "stream": stream,
                            "classes": by_band[band],
                            "hsc_papers": subject.hsc_papers if band == "hsc" else 1,
                        }
                    )
    return rows


def coverage(items: list[dict]) -> dict:
    """Count items against every catalog slot. Empty slots stay visible."""
    counts: dict[tuple, int] = {}
    verified: dict[tuple, int] = {}
    for item in items:
        if not isinstance(item, dict) or item.get("subject") not in SUBJECTS:
            continue
        band = class_band(item.get("class_level"))
        if band is None:
            continue
        try:
            stream = resolve_stream(item)
        except (KeyError, ValueError, TypeError):
            continue
        key = (item["subject"], band, stream)
        counts[key] = counts.get(key, 0) + 1
        if item.get("verified") is True:
            verified[key] = verified.get(key, 0) + 1
    slots = []
    for row in catalog_slots():
        key = (row["subject"], row["class_band"], row["stream"])
        slots.append({**row, "n_items": counts.get(key, 0), "n_verified": verified.get(key, 0)})
    by_band = {}
    for band in BAND_ORDER:
        band_slots = [s for s in slots if s["class_band"] == band]
        by_band[band] = {
            "slots": len(band_slots),
            "with_items": sum(1 for s in band_slots if s["n_items"]),
            "verified": sum(1 for s in band_slots if s["n_verified"]),
        }
    return {
        "n_subjects": len(SUBJECTS),
        "n_slots": len(slots),
        "n_slots_with_items": sum(1 for s in slots if s["n_items"]),
        "n_slots_verified": sum(1 for s in slots if s["n_verified"]),
        "by_band": by_band,
        "slots": slots,
    }


def render_subjects_markdown() -> str:
    """Human catalog. Tests require docs/subjects.md to match this text."""
    lines = [
        "# Subjects the harness can score",
        "",
        "Class 5 through college (class 11–12). Science, commerce (ব্যবসায় শিক্ষা)",
        "and arts (মানবিক) are all first-class. A slot with no question file yet is",
        "still a slot: `banglaedu-bench coverage` prints the empty ones.",
        "",
        "College subjects of two papers use paper 1 in class 11 and paper 2 in class 12.",
        "ICT at HSC is one paper. Class 5 has MCQ and short answer only.",
        "",
        "| Subject | Bangla | Classes | Streams | College papers |",
        "|---|---|---|---|---|",
    ]
    for subject in SUBJECTS.values():
        classes = sorted({c for offer in subject.offers for c in offer.classes})
        streams = []
        for offer in subject.offers:
            for stream in offer.streams:
                if stream not in streams:
                    streams.append(stream)
        class_text = ", ".join(str(c) for c in classes)
        stream_text = ", ".join(streams)
        papers = str(subject.hsc_papers) if 11 in classes else "—"
        lines.append(
            f"| `{subject.key}` | {subject.name_bn} | {class_text} | {stream_text} | {papers} |"
        )
    lines.append("")
    return "\n".join(lines)
