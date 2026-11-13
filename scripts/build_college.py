"""Build the public college seed (schema 0.2).

These items are original. They are not textbook exercises and not board papers.
Chapter numbers follow the commonly published NCTB HSC books. Topic ids are
provisional until a teacher aligns them with nctb-data. Every item stays
verified=false.

Run from the repo root: uv run python scripts/build_college.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banglaedu_bench import CANARY  # noqa: E402
from banglaedu_bench.curriculum import SUBJECTS  # noqa: E402
from banglaedu_bench.loader import COLLEGE_PATH, write_jsonl  # noqa: E402
from banglaedu_bench.schema import validate_items  # noqa: E402
from banglaedu_bench.verify import check_items  # noqa: E402

VERSION = "0.2.0"
CREATED = "2026-11-13"
DATA_LICENSE = "CC BY 4.0"
LICENSE = DATA_LICENSE
AUTHOR = "BanglaEdu Bench maintainers (drafted for Nasir Khan, GitHub Imnasir-X)"
LABELS = ("ক", "খ", "গ", "ঘ")


def _base(
    subject: str, classes: list[int], stream: str, paper, chapter: int, title: str, topic: int
):
    code = SUBJECTS[subject].topic_code
    language = "en" if subject == "english" else "bn"
    return {
        "subject": subject,
        "code": code,
        "classes": classes,
        "stream": stream,
        "paper": paper,
        "chapter": chapter,
        "title": title,
        "language": language,
        "topic_id": f"nctb:{code}:c11-12:{language}:ch{chapter:02d}:t{topic:02d}",
    }


class Bank:
    def __init__(self) -> None:
        self._n: dict[str, int] = {}
        self.items: list[dict] = []

    def _id(self, code: str) -> str:
        self._n[code] = self._n.get(code, 0) + 1
        return f"bebench-{code}-c11-12-{self._n[code]:03d}"

    def _finish(self, meta: dict, body: dict) -> None:
        name = SUBJECTS[meta["subject"]].name_bn
        paper = f", paper {meta['paper']}" if meta["paper"] else ""
        item = {
            "id": self._id(meta["code"]),
            "version": VERSION,
            "schema_version": "0.2",
            "canary": CANARY,
            "language": meta["language"],
            "class_level": meta["classes"],
            "subject": meta["subject"],
            "stream": meta["stream"],
            "chapter": {
                "number": meta["chapter"],
                "title_bn": meta["title"],
                "edition": "NCTB HSC",
            },
            "topic_id": meta["topic_id"],
            "topic_id_status": "provisional",
            "verified": False,
            "review": {"reviewers": [], "final_verdict": "pending"},
            "split": "college",
            "source": {
                "type": "original_syllabus_aligned",
                "citation": (
                    f"Original item written for BanglaEdu Bench college seed ({CREATED}); "
                    f"aligned to the NCTB HSC syllabus for {name}, class {meta['classes']}"
                    f"{paper}, chapter {meta['chapter']} '{meta['title']}'. "
                    "Not copied from any textbook exercise or education-board question paper."
                ),
                "author": AUTHOR,
                "created": CREATED,
                "license": LICENSE,
                "syllabus_reference": "NCTB higher secondary syllabus, class 11-12.",
            },
        }
        if meta["paper"] is not None:
            item["paper"] = meta["paper"]
        item.update(body)
        self.items.append(item)

    def mcq(
        self,
        subject,
        classes,
        stream,
        paper,
        chapter,
        title,
        topic,
        question,
        options,
        label,
        explanation,
        expression=None,
        difficulty="easy",
        thinking="knowledge",
    ):
        meta = _base(subject, classes, stream, paper, chapter, title, topic)
        check: dict = {"method": "author_subject_knowledge"}
        if expression is not None:
            check = {
                "method": "python_expression",
                "expression": expression,
                "option_rel_tol": 0.01,
            }
        self._finish(
            meta,
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
                "difficulty": difficulty,
                "thinking_level": thinking,
                "answer_check": check,
            },
        )

    def short(
        self,
        subject,
        classes,
        stream,
        paper,
        chapter,
        title,
        topic,
        question,
        text,
        explanation,
        aliases=None,
        numeric=None,
        expression=None,
        marks=1,
        difficulty="easy",
        thinking="application",
    ):
        meta = _base(subject, classes, stream, paper, chapter, title, topic)
        key: dict = {"text": text, "aliases": list(aliases or [])}
        check: dict = {"method": "author_subject_knowledge"}
        if numeric is not None:
            value, unit = numeric
            key["numeric"] = {"value": value, "unit": unit, "rel_tol": 0.01, "abs_tol": 0.0}
            check = {"method": "python_expression", "expression": expression}
        self._finish(
            meta,
            {
                "task_type": "short_answer",
                "question": question,
                "answer_key": key,
                "marking_rubric": [{"criterion": "সঠিক উত্তর", "marks": marks}],
                "max_marks": marks,
                "explanation": explanation,
                "difficulty": difficulty,
                "thinking_level": thinking,
                "answer_check": check,
            },
        )


def build_items() -> list[dict]:
    b = Bank()
    # --- science ---
    b.mcq(
        "physics",
        [11],
        "science",
        1,
        4,
        "নিউটনীয় বলবিদ্যা",
        1,
        "৩ kg ভরের একটি বস্তুতে ৪ m s⁻² ত্বরণ সৃষ্টি করতে কত বল লাগে?",
        ["১২ N", "৭ N", "০.৭৫ N", "৪৮ N"],
        "ক",
        "F = ma = ৩ × ৪ = ১২ N।",
        expression="3*4",
        thinking="application",
    )
    b.short(
        "physics",
        [11],
        "science",
        1,
        6,
        "মহাকর্ষ ও অভিকর্ষ",
        1,
        "২ kg ভরের একটি বস্তুর ওজন কত? (g = ৯.৮ m s⁻²)",
        "ওজন = mg = ২ × ৯.৮ = ১৯.৬ N",
        "ওজন = mg = ১৯.৬ N।",
        numeric=(19.6, "N"),
        expression="2*9.8",
    )
    b.mcq(
        "physics",
        [12],
        "science",
        2,
        2,
        "স্থির তড়িৎ",
        1,
        "দুটি বিন্দু আধানের দূরত্ব দ্বিগুণ করলে কুলম্ব বল কত অংশে নেমে আসে?",
        ["অর্ধেক", "দ্বিগুণ", "এক-চতুর্থাংশ", "চারগুণ"],
        "গ",
        "F ∝ 1/r²। r দ্বিগুণ হলে বল আগের এক-চতুর্থাংশ হয়।",
        thinking="application",
        difficulty="medium",
    )
    _physics_motion(b)

    b.mcq(
        "chemistry",
        [11],
        "science",
        1,
        3,
        "মৌলের পর্যায়বৃত্ত ধর্ম",
        1,
        "তৃতীয় পর্যায়ে বাম থেকে ডানে পারমাণবিক ব্যাসার্ধের সাধারণ প্রবণতা কোনটি?",
        ["বাড়ে", "কমে", "অপরিবর্তিত থাকে", "প্রথমে কমে তারপর দ্বিগুণ হয়"],
        "খ",
        "একই পর্যায়ে নিউক্লিয়াসের আধান বাড়ে, তাই পরমাণু সংকুচিত হয় এবং ব্যাসার্ধ কমে।",
    )
    b.short(
        "chemistry",
        [12],
        "science",
        2,
        3,
        "পরিমাণগত রসায়ন",
        1,
        "৩৬ গ্রাম পানিতে কত মোল আছে? (পানির আণবিক ভর ১৮ g mol⁻¹)",
        "মোল সংখ্যা = ৩৬/১৮ = ২ mol",
        "n = m/M = ২ mol।",
        numeric=(2.0, "mol"),
        expression="36/18",
    )
    b.mcq(
        "chemistry",
        [12],
        "science",
        2,
        2,
        "জৈব রসায়ন",
        1,
        "অ্যালকোহলের কার্যকরী মূলক কোনটি?",
        ["−OH", "−CHO", "−COOH", "−NH₂"],
        "ক",
        "অ্যালকোহলের কার্যকরী মূলক হাইড্রক্সিল (−OH)। অ্যালডিহাইড −CHO, কার্বক্সিলিক অ্যাসিড −COOH, অ্যামিন −NH₂।",
    )

    b.mcq(
        "biology",
        [11],
        "science",
        1,
        1,
        "কোষ ও এর গঠন",
        1,
        "কোষের কোন অঙ্গাণুকে শক্তিঘর বলা হয়?",
        ["মাইটোকন্ড্রিয়া", "রাইবোজোম", "গলজি বডি", "লাইসোজোম"],
        "ক",
        "মাইটোকন্ড্রিয়ায় কোষীয় শ্বসনের মাধ্যমে ATP তৈরি হয়, তাই একে শক্তিঘর বলে।",
    )
    b.short(
        "biology",
        [11],
        "science",
        1,
        1,
        "কোষ ও এর গঠন",
        2,
        "মাইটোকন্ড্রিয়াকে কোষের শক্তিঘর বলা হয় কেন? এক বাক্যে লেখ।",
        "মাইটোকন্ড্রিয়ায় কোষীয় শ্বসনে ATP তৈরি হয় বলে একে শক্তিঘর বলে।",
        "শক্তিঘর নামের কারণ ATP উৎপাদন।",
        marks=2,
        thinking="comprehension",
    )
    b.mcq(
        "biology",
        [12],
        "science",
        2,
        11,
        "জিনতত্ত্ব ও বিবর্তন",
        1,
        "DNA-তে অ্যাডেনিনের পরিপূরক ক্ষারক কোনটি?",
        ["থাইমিন", "গুয়ানিন", "ইউরাসিল", "অ্যাডেনিন"],
        "ক",
        "DNA-তে অ্যাডেনিন থাইমিনের সাথে জোড়া বাঁধে। গুয়ানিন সাইটোসিনের সাথে। ইউরাসিল RNA-তে থাকে।",
    )

    b.short(
        "higher_mathematics",
        [11],
        "science",
        1,
        1,
        "ম্যাট্রিক্স ও নির্ণায়ক",
        1,
        "a₁₁=২, a₁₂=১, a₂₁=০, a₂₂=৪ হলে ২×২ ম্যাট্রিক্সটির নির্ণায়ক কত?",
        "নির্ণায়ক = a₁₁ a₂₂ − a₁₂ a₂₁ = ৮ − ০ = ৮",
        "নির্ণায়ক ৮।",
        numeric=(8.0, ""),
        expression="2*4 - 1*0",
    )
    b.short(
        "higher_mathematics",
        [11],
        "science",
        1,
        7,
        "অন্তরীকরণ",
        1,
        "y = x³ হলে x = ২ বিন্দুতে dy/dx কত?",
        "dy/dx = ৩x²। x = ২ হলে মান ১২।",
        "৩ × ২² = ১২।",
        numeric=(12.0, ""),
        expression="3*2**2",
    )
    b.short(
        "higher_mathematics",
        [12],
        "science",
        2,
        1,
        "যোগজীকরণ",
        1,
        "০ থেকে ৩ পর্যন্ত 2x এর সমাকলন কত?",
        "∫ 2x dx = x²। ৩² − ০² = ৯।",
        "নির্দিষ্ট সমাকলনের মান ৯।",
        numeric=(9.0, ""),
        expression="3**2 - 0**2",
    )

    # --- commerce ---
    b.short(
        "accounting",
        [11],
        "commerce",
        1,
        1,
        "হিসাববিজ্ঞান পরিচিতি",
        1,
        "সম্পদ ৮০০০০ টাকা এবং দায় ৩০০০০ টাকা হলে মালিকানা স্বত্ব কত টাকা?",
        "মালিকানা স্বত্ব = সম্পদ − দায় = ৫০০০০ টাকা",
        "A = L + E, তাই E = ৫০০০০।",
        numeric=(50000.0, "টাকা"),
        expression="80000-30000",
    )
    b.short(
        "accounting",
        [11],
        "commerce",
        1,
        8,
        "দৃশ্যমান ও অদৃশ্যমান সম্পদের হিসাবরক্ষণ",
        1,
        "একটি যন্ত্রের ক্রয়মূল্য ৫০০০০ টাকা, ভগ্নাংশ মূল্য ৫০০০ টাকা এবং আয়ু ৫ বছর। সরলরৈখিক পদ্ধতিতে বার্ষিক অবচয় কত টাকা?",
        "বার্ষিক অবচয় = (৫০০০০ − ৫০০০) / ৫ = ৯০০০ টাকা",
        "সরলরৈখিক অবচয় ৯০০০ টাকা।",
        numeric=(9000.0, "টাকা"),
        expression="(50000-5000)/5",
    )
    b.short(
        "accounting",
        [12],
        "commerce",
        2,
        2,
        "অংশীদারি ব্যবসায়ের হিসাব",
        1,
        "অ ও ব এর মূলধন অনুপাত ৩:২। বছরের মুনাফা ১৫০০০ টাকা হলে অ এর অংশ কত টাকা?",
        "অ এর অংশ = ১৫০০০ × ৩/৫ = ৯০০০ টাকা",
        "৩/৫ অংশ ৯০০০ টাকা।",
        numeric=(9000.0, "টাকা"),
        expression="15000*3/5",
    )

    b.mcq(
        "business_organization",
        [11],
        "commerce",
        1,
        1,
        "ব্যবসায়ের মৌলিক ধারণা",
        1,
        "একমালিকানা ব্যবসায়ের মালিকের দায় কীরূপ?",
        ["অসীম", "সীমিত", "নেই", "কেবল সরকার বহন করে"],
        "ক",
        "একমালিকানা ব্যবসায়ে মালিকের দায় অসীম। কোম্পানির শেয়ারহোল্ডারের দায় সীমিত।",
    )
    b.mcq(
        "business_organization",
        [11],
        "commerce",
        1,
        4,
        "অংশীদারি ব্যবসায়",
        1,
        "কমপক্ষে কতজন ব্যক্তি নিয়ে অংশীদারি ব্যবসায় গঠিত হয়?",
        ["১ জন", "২ জন", "৭ জন", "১০ জন"],
        "খ",
        "অংশীদারি ব্যবসায় কমপক্ষে দুইজনের চুক্তিতে গঠিত হয়।",
    )
    b.mcq(
        "business_organization",
        [12],
        "commerce",
        2,
        1,
        "ব্যবস্থাপনার পরিচিতি",
        1,
        "নিচের কোনটি ব্যবস্থাপনার কাজ?",
        ["পরিকল্পনা", "রেওয়ামিল তৈরি", "অবচয় ধার্য", "ব্যাংক সমন্বয়"],
        "ক",
        "পরিকল্পনা, সংগঠিতকরণ, প্রেষণা বা নেতৃত্ব এবং নিয়ন্ত্রণ ব্যবস্থাপনার কাজ। রেওয়ামিল ও অবচয় হিসাববিজ্ঞানের কাজ।",
    )

    b.short(
        "finance_banking_insurance",
        [11],
        "commerce",
        1,
        1,
        "অর্থ",
        1,
        "৫০০০ টাকার ওপর বার্ষিক ৮% সরল সুদে ৩ বছরের সুদ কত টাকা?",
        "সুদ = ৫০০০ × ৮ × ৩ / ১০০ = ১২০০ টাকা",
        "I = Pnr/100 = ১২০০।",
        numeric=(1200.0, "টাকা"),
        expression="5000*8*3/100",
    )
    b.short(
        "finance_banking_insurance",
        [12],
        "commerce",
        2,
        1,
        "কেন্দ্রীয় ব্যাংক",
        1,
        "বাংলাদেশের কেন্দ্রীয় ব্যাংকের নাম কী?",
        "বাংলাদেশ ব্যাংক",
        "বাংলাদেশের কেন্দ্রীয় ব্যাংক বাংলাদেশ ব্যাংক।",
        aliases=["Bangladesh Bank"],
        thinking="knowledge",
    )
    b.mcq(
        "finance_banking_insurance",
        [12],
        "commerce",
        2,
        3,
        "বীমা",
        1,
        "বীমার যে নীতিতে বীমাগ্রহীতা ঝুঁকির গুরুত্বপূর্ণ তথ্য গোপন করবেন না, সেটি কোনটি?",
        ["চরম সততা", "চাহিদার সূত্র", "সরলরৈখিক অবচয়", "রেওয়ামিল"],
        "ক",
        "চরম সততা (utmost good faith) বীমার একটি মূলনীতি।",
        thinking="knowledge",
    )

    # --- arts ---
    b.mcq(
        "history",
        [11],
        "arts",
        1,
        1,
        "বাংলাদেশের ইতিহাস",
        1,
        "ভাষা আন্দোলনের শহিদ দিবস কোন তারিখ?",
        ["২১ ফেব্রুয়ারি ১৯৫২", "২৬ মার্চ ১৯৭১", "১৬ ডিসেম্বর ১৯৭১", "৪ নভেম্বর ১৯৭২"],
        "ক",
        "১৯৫২ সালের ২১ ফেব্রুয়ারি ভাষা আন্দোলনের শহিদ দিবস।",
        thinking="knowledge",
    )
    b.mcq(
        "history",
        [12],
        "arts",
        2,
        2,
        "মুক্তিযুদ্ধ",
        1,
        "বাংলাদেশের স্বাধীনতা ঘোষণার তারিখ হিসেবে কোনটি গৃহীত?",
        ["২১ ফেব্রুয়ারি ১৯৫২", "৭ মার্চ ১৯৭১", "২৬ মার্চ ১৯৭১", "১৬ ডিসেম্বর ১৯৭১"],
        "গ",
        "২৬ মার্চ ১৯৭১ স্বাধীনতা ঘোষণার তারিখ। ১৬ ডিসেম্বর বিজয় দিবস।",
        thinking="knowledge",
    )
    b.short(
        "history",
        [12],
        "arts",
        2,
        2,
        "মুক্তিযুদ্ধ",
        2,
        "বিজয় দিবস কোন তারিখ?",
        "১৬ ডিসেম্বর",
        "১৯৭১ সালের ১৬ ডিসেম্বর বিজয় দিবস।",
        aliases=["১৬ ডিসেম্বর ১৯৭১"],
        thinking="knowledge",
    )

    b.mcq(
        "civics_good_governance",
        [11],
        "arts",
        1,
        1,
        "সংবিধান",
        1,
        "বাংলাদেশের সংবিধান কোন তারিখে গৃহীত হয়?",
        ["১৬ ডিসেম্বর ১৯৭১", "৪ নভেম্বর ১৯৭২", "২৬ মার্চ ১৯৭১", "২১ ফেব্রুয়ারি ১৯৫২"],
        "খ",
        "সংবিধান ৪ নভেম্বর ১৯৭২ গৃহীত হয় এবং ১৬ ডিসেম্বর ১৯৭২ থেকে কার্যকর হয়।",
        thinking="knowledge",
    )
    b.mcq(
        "civics_good_governance",
        [11],
        "arts",
        1,
        2,
        "সরকারের অঙ্গ",
        1,
        "সরকারের অঙ্গ কয়টি?",
        ["২", "৩", "৪", "৫"],
        "খ",
        "আইন বিভাগ, নির্বাহী বিভাগ ও বিচার বিভাগ — সরকারের তিনটি অঙ্গ।",
        thinking="knowledge",
    )
    b.short(
        "civics_good_governance",
        [12],
        "arts",
        2,
        3,
        "মৌলিক অধিকার",
        1,
        "বাংলাদেশের সংবিধানে আইনের দৃষ্টিতে সমতা কোন অনুচ্ছেদে আছে? শুধু নম্বর লেখ।",
        "২৭",
        "অনুচ্ছেদ ২৭: আইনের দৃষ্টিতে সমতা এবং আইনের সমান আশ্রয়লাভের অধিকার।",
        aliases=["অনুচ্ছেদ ২৭", "article 27"],
        thinking="knowledge",
    )

    b.mcq(
        "logic",
        [11],
        "arts",
        1,
        2,
        "বচন",
        1,
        "যে বাক্য সত্য বা মিথ্যা হতে পারে তাকে কী বলে?",
        ["বচন", "পদ", "হেতুবাক্য", "উদাহরণ"],
        "ক",
        "সত্য বা মিথ্যা হওয়ার যোগ্য বাক্যই বচন। প্রশ্ন, আদেশ বা শুভেচ্ছা বচন নয়।",
        thinking="knowledge",
    )
    b.mcq(
        "logic",
        [11],
        "arts",
        1,
        2,
        "বচন",
        2,
        "«সকল মানুষ হয় মরণশীল» কোন জাতের বচন?",
        ["সার্বিক সদর্থক", "সার্বিক নঞর্থক", "বিশেষ সদর্থক", "বিশেষ নঞর্থক"],
        "ক",
        "«সকল S হয় P» সার্বিক সদর্থক বচন, ঐতিহ্যবাহী নাম A।",
        thinking="comprehension",
    )
    b.short(
        "logic",
        [12],
        "arts",
        2,
        3,
        "ন্যায়",
        1,
        "একটি নিরপেক্ষ ন্যায়ে কয়টি পদ থাকে?",
        "৩টি",
        "নিরপেক্ষ ন্যায়ে পক্ষপদ, সাধ্যপদ ও হেতুপদ — মোট তিনটি পদ।",
        aliases=["তিনটি", "৩"],
        thinking="knowledge",
    )

    b.mcq(
        "economics",
        [11],
        "arts",
        1,
        2,
        "চাহিদা",
        1,
        "অন্যান্য অবস্থা স্থির থাকলে দাম বাড়লে চাহিদার পরিমাণ কমে। এটি কোন সূত্র?",
        ["চাহিদার সূত্র", "যোগানের সূত্র", "ক্রমহ্রাসমান প্রান্তিক উপযোগ", "মুদ্রার পরিমাণ তত্ত্ব"],
        "ক",
        "দাম ও চাহিদার পরিমাণের বিপরীত সম্পর্ক চাহিদার সূত্র।",
        thinking="knowledge",
    )
    b.short(
        "economics",
        [11],
        "arts",
        1,
        2,
        "চাহিদা",
        2,
        "একটি দ্রব্যের দাম ১০% বাড়লে চাহিদার পরিমাণ ২০% কমে। চাহিদার দাম স্থিতিস্থাপকতার পরম মান কত?",
        "স্থিতিস্থাপকতার পরম মান = ২০/১০ = ২",
        "|Ed| = ২।",
        numeric=(2.0, ""),
        expression="20/10",
        difficulty="medium",
    )
    b.short(
        "economics",
        [12],
        "commerce",
        2,
        1,
        "অর্থনীতির পরিচিতি",
        1,
        "পরবর্তী সর্বোত্তম বিকল্পের জন্য যে মূল্য ত্যাগ করা হয় তাকে কী বলে?",
        "সুযোগ ব্যয়",
        "সুযোগ ব্যয় হলো পরবর্তী সর্বোত্তম বিকল্পের ত্যাগকৃত মূল্য।",
        aliases=["সুযোগব্যয়", "opportunity cost"],
        thinking="knowledge",
    )

    # --- every college student ---
    b.mcq(
        "bangla",
        [11],
        "common",
        1,
        1,
        "ছন্দ",
        1,
        "নিচের কোনটি বাংলা ছন্দের প্রকার নয়?",
        ["অক্ষরবৃত্ত", "মাত্রাবৃত্ত", "স্বরবৃত্ত", "স্পেনসারিয়ান"],
        "ঘ",
        "বাংলা ছন্দের তিনটি প্রধান প্রকার অক্ষরবৃত্ত, মাত্রাবৃত্ত ও স্বরবৃত্ত। স্পেনসারিয়ান ইংরেজি সনেটের একটি রূপ।",
        thinking="knowledge",
    )
    b.mcq(
        "bangla",
        [12],
        "common",
        2,
        1,
        "সন্ধি",
        1,
        "হিম + আলয় = হিমালয় কোন সন্ধি?",
        ["স্বরসন্ধি", "ব্যঞ্জনসন্ধি", "বিসর্গ সন্ধি", "লোপ সন্ধি"],
        "ক",
        "স্বরধ্বনি অ-এর সাথে আ মিলে স্বরসন্ধি হয়েছে।",
        thinking="application",
    )
    b.short(
        "bangla",
        [12],
        "common",
        2,
        3,
        "কারক",
        1,
        "ক্রিয়ার ফল যে পদে পড়ে তাকে কী বলে?",
        "কর্ম",
        "ক্রিয়ার ফল যার ওপর পড়ে সেই পদ কর্ম কারক।",
        aliases=["কর্মকারক"],
        thinking="knowledge",
    )

    b.mcq(
        "english",
        [11],
        "common",
        1,
        1,
        "Grammar",
        1,
        "Choose the correct verb: She ___ to college every day.",
        ["goes", "go", "gone", "going"],
        "ক",
        "With a singular third-person subject in the simple present, the verb takes -es: goes.",
        thinking="application",
    )
    b.mcq(
        "english",
        [11],
        "common",
        1,
        2,
        "Grammar",
        1,
        "Choose the passive form of 'They write letters.'",
        [
            "Letters are written by them.",
            "Letters were written by them.",
            "Letters written by them.",
            "Letters are writing by them.",
        ],
        "ক",
        "Simple present passive is am/is/are + past participle: are written.",
        thinking="application",
    )
    b.short(
        "english",
        [12],
        "common",
        2,
        1,
        "Grammar",
        1,
        "Name the tense of this sentence: I am reading a book now.",
        "present continuous",
        "am/is/are + verb-ing is the present continuous tense.",
        aliases=["present continuous tense"],
        thinking="knowledge",
    )

    b.short(
        "ict",
        [11],
        "common",
        None,
        3,
        "সংখ্যা পদ্ধতি",
        1,
        "দ্বিমিক সংখ্যা ১১০১ এর দশমিক মান কত?",
        "১×৮ + ১×৪ + ০×২ + ১×১ = ১৩",
        "১১০১₂ = ১৩₁₀।",
        numeric=(13.0, ""),
        expression="1*8 + 1*4 + 0*2 + 1*1",
    )
    b.mcq(
        "ict",
        [11],
        "common",
        None,
        1,
        "তথ্য ও যোগাযোগ প্রযুক্তি",
        1,
        "১ বাইট কত বিট?",
        ["৪", "৮", "১৬", "৩২"],
        "খ",
        "১ বাইট = ৮ বিট।",
        expression="8",
        thinking="knowledge",
    )
    b.short(
        "ict",
        [12],
        "common",
        None,
        5,
        "ইন্টারনেট",
        1,
        "HTTP এর পূর্ণরূপ কী?",
        "hypertext transfer protocol",
        "HTTP মানে Hypertext Transfer Protocol।",
        aliases=["Hypertext Transfer Protocol"],
        thinking="knowledge",
    )
    return b.items


def _physics_motion(b: Bank) -> None:
    """One creative question so the college seed uses the board's four parts."""

    def part(label, level, marks, question, text, numeric=None, expression=None):
        key: dict = {"text": text, "aliases": []}
        check: dict = {"method": "author_subject_knowledge"}
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
        part("ক", "knowledge", 1, "ত্বরণ কাকে বলে?", "সময়ের সাথে বেগের পরিবর্তনের হারকে ত্বরণ বলে।"),
        part(
            "খ",
            "comprehension",
            2,
            "স্থির অবস্থা থেকে যাত্রা শুরু করলে আদিবেগ শূন্য ধরা হয় কেন?",
            "স্থির বস্তুর বেগ শূন্য, তাই যাত্রার মুহূর্তে আদিবেগ u = 0।",
        ),
        part(
            "গ",
            "application",
            3,
            "৫ সেকেন্ড পরে বস্তুটির বেগ নির্ণয় কর।",
            "v = u + at = ০ + ২ × ৫ = ১০ m s⁻¹",
            numeric=(10.0, "m s⁻¹"),
            expression="0 + 2*5",
        ),
        part(
            "ঘ",
            "higher_ability",
            4,
            "অতিক্রান্ত দূরত্ব নির্ণয় কর এবং দেখাও যে এই দূরত্ব শেষ বেগ ও সময়ের গুণফলের অর্ধেক।",
            "s = ut + ½at² = ০ + ½ × ২ × ৫² = ২৫ m। vt/2 = ১০ × ৫ / ২ = ২৫ m, তাই দুটি সমান।",
            numeric=(25.0, "m"),
            expression="0.5*2*5**2",
        ),
    ]
    meta = _base("physics", [11], "science", 1, 3, "গতিবিদ্যা", 1)
    b._finish(
        meta,
        {
            "task_type": "srijonshil",
            "question": "একটি বস্তু স্থির অবস্থা থেকে যাত্রা শুরু করে ৫ s ধরে ২ m s⁻² সুষম ত্বরণে চলে।",
            "answer_key": {"parts": {p["label"]: p["answer_key"]["text"] for p in parts}},
            "marking_rubric": [
                {"criterion": "(ক) knowledge", "marks": 1},
                {"criterion": "(খ) comprehension", "marks": 2},
                {"criterion": "(গ) application", "marks": 3},
                {"criterion": "(ঘ) higher_ability", "marks": 4},
            ],
            "max_marks": 10,
            "explanation": "v = ১০ m s⁻¹ এবং s = ২৫ m। s = vt/2 যখন u = 0।",
            "difficulty": "medium",
            "thinking_level": "higher_ability",
            "answer_check": {"method": "author_subject_knowledge"},
            "parts": parts,
        },
    )


def main() -> None:
    items = build_items()
    errs = validate_items(items)
    n, verr = check_items(items)
    errs += verr
    if errs:
        for err in errs:
            print(err)
        raise SystemExit(1)
    write_jsonl(COLLEGE_PATH, items)
    print(f"wrote {len(items)} items, {n} numeric keys checked, to {COLLEGE_PATH}")


if __name__ == "__main__":
    main()
