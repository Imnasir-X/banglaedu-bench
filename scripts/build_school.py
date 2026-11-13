"""Build the public class 5 and class 6–8 seeds (schema 0.2).

Original items only. Topic ids are provisional: nctb-data 0.1.0 has no
primary or junior book. Nothing here is verified.

Run from the repo root: uv run python scripts/build_school.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banglaedu_bench import CANARY  # noqa: E402
from banglaedu_bench.curriculum import SUBJECTS  # noqa: E402
from banglaedu_bench.loader import JUNIOR_PATH, PRIMARY_PATH, write_jsonl  # noqa: E402
from banglaedu_bench.schema import validate_items  # noqa: E402
from banglaedu_bench.verify import check_items  # noqa: E402

VERSION = "0.2.0"
CREATED = "2026-11-13"
DATA_LICENSE = "CC BY 4.0"
AUTHOR = "BanglaEdu Bench maintainers (drafted for Nasir Khan, GitHub Imnasir-X)"
LABELS = ("ক", "খ", "গ", "ঘ")


class Bank:
    def __init__(self, split: str, band: str) -> None:
        self.split = split
        self.band = band
        self._n: dict[str, int] = {}
        self.items: list[dict] = []

    def _id(self, code: str) -> str:
        self._n[code] = self._n.get(code, 0) + 1
        span = "c5" if self.band == "primary" else "c6-8"
        return f"bebench-{code}-{span}-{self._n[code]:03d}"

    def _add(
        self, subject: str, classes: list[int], chapter: int, title: str, topic: int, body: dict
    ):
        code = SUBJECTS[subject].topic_code
        language = "en" if subject == "english" else "bn"
        name = SUBJECTS[subject].name_bn
        span = "c5" if self.band == "primary" else "c6-8"
        item = {
            "id": self._id(code),
            "version": VERSION,
            "schema_version": "0.2",
            "canary": CANARY,
            "language": language,
            "class_level": classes,
            "subject": subject,
            "stream": "common",
            "chapter": {"number": chapter, "title_bn": title, "edition": "NCTB school"},
            "topic_id": f"nctb:{code}:{span}:{language}:ch{chapter:02d}:t{topic:02d}",
            "topic_id_status": "provisional",
            "verified": False,
            "review": {"reviewers": [], "final_verdict": "pending"},
            "split": self.split,
            "source": {
                "type": "original_syllabus_aligned",
                "citation": (
                    f"Original item written for BanglaEdu Bench school seed ({CREATED}); "
                    f"aligned to the NCTB {name} syllabus, class {classes}, "
                    f"chapter {chapter} '{title}'. "
                    "Not copied from any textbook exercise or education-board question paper."
                ),
                "author": AUTHOR,
                "created": CREATED,
                "license": DATA_LICENSE,
                "syllabus_reference": "NCTB primary and junior syllabus. Topic ids are provisional.",
            },
        }
        item.update(body)
        self.items.append(item)

    def mcq(
        self,
        subject,
        classes,
        chapter,
        title,
        topic,
        question,
        options,
        label,
        explanation,
        expression=None,
        thinking="knowledge",
    ):
        check = {"method": "author_subject_knowledge"}
        if expression is not None:
            check = {
                "method": "python_expression",
                "expression": expression,
                "option_rel_tol": 0.01,
            }
        self._add(
            subject,
            classes,
            chapter,
            title,
            topic,
            {
                "task_type": "mcq",
                "question": question,
                "options": [
                    {"label": lab, "text": text} for lab, text in zip(LABELS, options, strict=True)
                ],
                "answer_key": {"label": label},
                "marking_rubric": [{"criterion": "সঠিক বিকল্প", "marks": 1}],
                "max_marks": 1,
                "explanation": explanation,
                "difficulty": "easy",
                "thinking_level": thinking,
                "answer_check": check,
            },
        )

    def short(
        self,
        subject,
        classes,
        chapter,
        title,
        topic,
        question,
        text,
        explanation,
        aliases=None,
        numeric=None,
        expression=None,
        thinking="application",
    ):
        key = {"text": text, "aliases": list(aliases or [])}
        check = {"method": "author_subject_knowledge"}
        if numeric is not None:
            value, unit = numeric
            key["numeric"] = {"value": value, "unit": unit, "rel_tol": 0.01, "abs_tol": 0.0}
            check = {"method": "python_expression", "expression": expression}
        self._add(
            subject,
            classes,
            chapter,
            title,
            topic,
            {
                "task_type": "short_answer",
                "question": question,
                "answer_key": key,
                "marking_rubric": [{"criterion": "সঠিক উত্তর", "marks": 1}],
                "max_marks": 1,
                "explanation": explanation,
                "difficulty": "easy",
                "thinking_level": thinking,
                "answer_check": check,
            },
        )


def build_primary() -> list[dict]:
    b = Bank("primary", "primary")
    c5 = [5]
    b.mcq(
        "mathematics",
        c5,
        2,
        "যোগ ও বিয়োগ",
        1,
        "১২৫ + ৮৭ কত?",
        ["২১২", "২০২", "১১২", "২১২০"],
        "ক",
        "১২৫ + ৮৭ = ২১২।",
        expression="125+87",
        thinking="application",
    )
    b.short(
        "mathematics",
        c5,
        4,
        "ক্ষেত্রফল",
        1,
        "৮ মিটার লম্বা ও ৫ মিটার চওড়া একটি আয়তক্ষেত্রের ক্ষেত্রফল কত বর্গমিটার?",
        "ক্ষেত্রফল = ৮ × ৫ = ৪০ বর্গমিটার",
        "৪০ বর্গমিটার।",
        numeric=(40.0, "বর্গমিটার"),
        expression="8*5",
    )
    b.short(
        "mathematics",
        c5,
        3,
        "গুণ ও ভাগ",
        1,
        "৩৬ এর অর্ধেক কত?",
        "৩৬ ÷ ২ = ১৮",
        "১৮।",
        numeric=(18.0, ""),
        expression="36/2",
    )
    b.mcq(
        "bangla",
        c5,
        1,
        "বিপরীত শব্দ",
        1,
        "«দিন» এর বিপরীত শব্দ কোনটি?",
        ["রাত", "সকাল", "আলো", "দুপুর"],
        "ক",
        "দিন এর বিপরীত শব্দ রাত।",
    )
    b.short(
        "bangla",
        c5,
        2,
        "পদ",
        1,
        "«কলম» কোন পদ?",
        "বিশেষ্য",
        "কলম একটি বস্তুর নাম, তাই বিশেষ্য।",
        aliases=["noun"],
        thinking="knowledge",
    )
    b.mcq(
        "english",
        c5,
        1,
        "Grammar",
        1,
        "Choose the plural of 'child'.",
        ["children", "childs", "childes", "child"],
        "ক",
        "The plural of child is children.",
    )
    b.short(
        "english",
        c5,
        2,
        "Vocabulary",
        1,
        "Write the opposite of 'hot'.",
        "cold",
        "The opposite of hot is cold.",
        thinking="knowledge",
    )
    b.mcq(
        "elementary_science",
        c5,
        3,
        "উদ্ভিদ",
        1,
        "উদ্ভিদ কোন প্রক্রিয়ায় নিজের খাদ্য তৈরি করে?",
        ["সালোকসংশ্লেষণ", "শ্বসন", "বাষ্পীভবন", "ঘনীভবন"],
        "ক",
        "উদ্ভিদ সালোকসংশ্লেষণে খাদ্য তৈরি করে।",
    )
    b.short(
        "elementary_science",
        c5,
        4,
        "পরিমাপ",
        1,
        "২ লিটার কত মিলিলিটার?",
        "২ × ১০০০ = ২০০০ মিলিলিটার",
        "২ লিটার = ২০০০ মিলিলিটার।",
        numeric=(2000.0, "মিলিলিটার"),
        expression="2*1000",
    )
    b.mcq(
        "bangladesh_and_global_studies",
        c5,
        1,
        "আমাদের দেশ",
        1,
        "বাংলাদেশের রাজধানী কোনটি?",
        ["ঢাকা", "চট্টগ্রাম", "খুলনা", "রাজশাহী"],
        "ক",
        "বাংলাদেশের রাজধানী ঢাকা।",
    )
    b.short(
        "bangladesh_and_global_studies",
        c5,
        2,
        "স্বাধীনতা",
        1,
        "বাংলাদেশ কোন সালে স্বাধীন হয়?",
        "১৯৭১",
        "বাংলাদেশ ১৯৭১ সালে স্বাধীন হয়।",
        aliases=["1971"],
        thinking="knowledge",
    )
    return b.items


def build_junior() -> list[dict]:
    b = Bank("junior", "junior")
    c = [6, 7, 8]
    b.short(
        "mathematics",
        c,
        5,
        "শতকরা",
        1,
        "১৫০ এর ২০% কত?",
        "১৫০ × ২০/১০০ = ৩০",
        "৩০।",
        numeric=(30.0, ""),
        expression="150*20/100",
    )
    b.short(
        "mathematics",
        c,
        2,
        "পূর্ণসংখ্যা",
        1,
        "(−৫) + ১২ কত?",
        "(−৫) + ১২ = ৭",
        "৭।",
        numeric=(7.0, ""),
        expression="-5+12",
    )
    b.mcq(
        "mathematics",
        c,
        3,
        "ভগ্নাংশ",
        1,
        "৩৬ এর ৩/৪ অংশ কত?",
        ["২৭", "২৪", "১২", "৪৮"],
        "ক",
        "৩৬ × ৩/৪ = ২৭।",
        expression="36*3/4",
        thinking="application",
    )
    b.mcq(
        "general_science",
        c,
        6,
        "শব্দ",
        1,
        "নিচের কোন মাধ্যমে শব্দ চলতে পারে না?",
        ["ইস্পাত", "পানি", "বায়ু", "শূন্যস্থান"],
        "ঘ",
        "শব্দের চলার জন্য মাধ্যম লাগে। শূন্যস্থানে শব্দ চলে না।",
    )
    b.short(
        "general_science",
        c,
        2,
        "গতি",
        1,
        "একটি সাইকেল ২০ সেকেন্ডে ১০০ মিটার গেল। সাইকেলটির দ্রুতি কত মিটার প্রতি সেকেন্ড?",
        "দ্রুতি = ১০০/২০ = ৫ m/s",
        "৫ m/s।",
        numeric=(5.0, "m/s"),
        expression="100/20",
    )
    b.mcq(
        "ict",
        c,
        1,
        "তথ্য",
        1,
        "একটি বাইটে কত বিট?",
        ["৪", "৮", "১৬", "৩২"],
        "খ",
        "১ বাইট = ৮ বিট।",
        expression="8",
    )
    b.short(
        "ict",
        c,
        3,
        "সংখ্যা পদ্ধতি",
        1,
        "দ্বিমিক সংখ্যা ১০১১ এর দশমিক মান কত?",
        "১×৮ + ০×৪ + ১×২ + ১×১ = ১১",
        "১১।",
        numeric=(11.0, ""),
        expression="1*8+0*4+1*2+1",
    )
    b.mcq(
        "bangla",
        c,
        2,
        "পদ",
        1,
        "যে পদ দিয়ে কাজ বোঝায় তাকে কী বলে?",
        ["ক্রিয়া", "বিশেষ্য", "বিশেষণ", "সর্বনাম"],
        "ক",
        "কাজ বোঝালে সেই পদ ক্রিয়া।",
    )
    b.short(
        "bangla",
        c,
        1,
        "বিপরীত শব্দ",
        1,
        "«বড়» এর বিপরীত শব্দ কী?",
        "ছোট",
        "বড় এর বিপরীত শব্দ ছোট।",
        aliases=["ক্ষুদ্র"],
        thinking="knowledge",
    )
    b.mcq(
        "english",
        c,
        2,
        "Grammar",
        1,
        "Choose the past form of 'go'.",
        ["went", "goed", "gone", "going"],
        "ক",
        "The past form of go is went.",
    )
    b.short(
        "english",
        c,
        1,
        "Grammar",
        1,
        "Fill the gap with one word: She ___ a student.",
        "is",
        "She is a student.",
        thinking="application",
    )
    b.mcq(
        "bangladesh_and_global_studies",
        c,
        3,
        "জাতীয় প্রতীক",
        1,
        "বাংলাদেশের জাতীয় ফুল কোনটি?",
        ["শাপলা", "গোলাপ", "পদ্ম", "বেলি"],
        "ক",
        "বাংলাদেশের জাতীয় ফুল শাপলা।",
    )
    b.short(
        "bangladesh_and_global_studies",
        c,
        1,
        "রাজধানী",
        1,
        "জাতীয় সংসদ ভবন কোন শহরে?",
        "ঢাকা",
        "জাতীয় সংসদ ভবন ঢাকায়।",
        thinking="knowledge",
    )
    _speed_question(b, c)
    return b.items


def _speed_question(b: Bank, classes: list[int]) -> None:
    def part(label, level, marks, question, text, numeric=None, expression=None):
        key = {"text": text, "aliases": []}
        check = {"method": "author_subject_knowledge"}
        if numeric is not None:
            value, unit = numeric
            key["numeric"] = {"value": value, "unit": unit, "rel_tol": 0.01, "abs_tol": 0.0}
            check = {"method": "python_expression", "expression": expression}
        return {
            "label": label,
            "thinking_level": level,
            "marks": marks,
            "question": question,
            "answer_key": key,
            "marking_rubric": [{"criterion": "অংশের নির্ধারিত উত্তর", "marks": marks}],
            "answer_check": check,
        }

    parts = [
        part("ক", "knowledge", 1, "দ্রুতি কাকে বলে?", "একক সময়ে অতিক্রান্ত দূরত্বকে দ্রুতি বলে।"),
        part(
            "খ",
            "comprehension",
            2,
            "দ্রুতির সাথে বেগের একটি পার্থক্য লেখ।",
            "বেগের দিক আছে, দ্রুতির দিক নেই।",
        ),
        part(
            "গ",
            "application",
            3,
            "শিক্ষার্থীটির দ্রুতি নির্ণয় কর।",
            "দ্রুতি = ১০০/৫০ = ২ m/s",
            numeric=(2.0, "m/s"),
            expression="100/50",
        ),
        part(
            "ঘ",
            "higher_ability",
            4,
            "একই সময়ে ২০০ মিটার হাঁটলে দ্রুতি কত হত, এবং তা আগের দ্রুতির কত গুণ?",
            "২০০/৫০ = ৪ m/s, যা ২ m/s এর ২ গুণ।",
            numeric=(4.0, "m/s"),
            expression="200/50",
        ),
    ]
    b._add(
        "general_science",
        classes,
        2,
        "গতি",
        2,
        {
            "task_type": "srijonshil",
            "question": "একজন শিক্ষার্থী ৫০ সেকেন্ডে ১০০ মিটার হাঁটল।",
            "answer_key": {"parts": {p["label"]: p["answer_key"]["text"] for p in parts}},
            "marking_rubric": [
                {"criterion": "(ক) knowledge", "marks": 1},
                {"criterion": "(খ) comprehension", "marks": 2},
                {"criterion": "(গ) application", "marks": 3},
                {"criterion": "(ঘ) higher_ability", "marks": 4},
            ],
            "max_marks": 10,
            "explanation": "দ্রুতি ২ m/s। ২০০ মিটারে দ্রুতি ৪ m/s, যা দ্বিগুণ।",
            "difficulty": "medium",
            "thinking_level": "higher_ability",
            "answer_check": {"method": "author_subject_knowledge"},
            "parts": parts,
        },
    )


def main() -> None:
    primary, junior = build_primary(), build_junior()
    for name, items, path in (("primary", primary, PRIMARY_PATH), ("junior", junior, JUNIOR_PATH)):
        errs = validate_items(items)
        n, verr = check_items(items)
        errs += verr
        if errs:
            print(name)
            for err in errs:
                print(err)
            raise SystemExit(1)
        write_jsonl(path, items)
        print(f"wrote {len(items)} {name} items, {n} numeric keys, to {path}")


if __name__ == "__main__":
    main()
