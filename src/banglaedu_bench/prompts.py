"""Prompt templates (Bangla). Versioned: change PROMPT_VERSION whenever text changes."""

from __future__ import annotations

PROMPT_VERSION = "prompt-v0.1"

SYSTEM = (
    "তুমি বাংলাদেশের জাতীয় শিক্ষাক্রম (এনসিটিবি) অনুযায়ী নবম-দশম শ্রেণির পদার্থবিজ্ঞানের "
    "একজন দক্ষ শিক্ষার্থী। প্রশ্নের উত্তর বাংলায় দাও। প্রয়োজনে সংক্ষেপে হিসাব দেখাও। "
    "উত্তরের শেষ লাইনে অবশ্যই 'উত্তর: ' লিখে চূড়ান্ত উত্তর দেবে।"
)

GROUNDING_HEADER = (
    "নিচে পাঠ্যক্রমের প্রাসঙ্গিক অংশ দেওয়া হলো। প্রয়োজন হলে এটি ব্যবহার করো:\n"
    "<পাঠ্যক্রম>\n{context}\n</পাঠ্যক্রম>\n\n"
)

MCQ_INSTRUCTION = "নিচের বহুনির্বাচনি প্রশ্নের সঠিক উত্তর বেছে নাও। শেষ লাইনে শুধু 'উত্তর: ক/খ/গ/ঘ' লেখো।"
SHORT_INSTRUCTION = "নিচের প্রশ্নের সংক্ষিপ্ত উত্তর দাও।"
NUMERIC_INSTRUCTION = "নিচের প্রশ্নটি গাণিতিক। শেষ লাইনে 'উত্তর: <মান> <একক>' আকারে চূড়ান্ত মান লেখো।"
SRIJONSHIL_INSTRUCTION = "নিচে একটি সৃজনশীল প্রশ্নের উদ্দীপক ও একটি অংশ দেওয়া হলো। শুধু এই অংশের উত্তর দাও।"


def _wrap(body: str, grounding: str) -> list[dict]:
    prefix = GROUNDING_HEADER.format(context=grounding) if grounding else ""
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prefix + body}]


def mcq_messages(item: dict, grounding: str = "") -> list[dict]:
    opts = "\n".join(f"({o['label']}) {o['text']}" for o in item["options"])
    return _wrap(f"{MCQ_INSTRUCTION}\n\nপ্রশ্ন: {item['question']}\n{opts}", grounding)


def short_messages(item: dict, grounding: str = "") -> list[dict]:
    instr = NUMERIC_INSTRUCTION if "numeric" in item["answer_key"] else SHORT_INSTRUCTION
    return _wrap(f"{instr}\n\nপ্রশ্ন: {item['question']}", grounding)


def srijonshil_messages(item: dict, part: dict, grounding: str = "") -> list[dict]:
    instr = SRIJONSHIL_INSTRUCTION
    if "numeric" in part["answer_key"]:
        instr += " শেষ লাইনে 'উত্তর: <মান> <একক>' আকারে চূড়ান্ত মান লেখো।"
    body = f"{instr}\n\nউদ্দীপক: {item['question']}\n\n({part['label']}) {part['question']}"
    return _wrap(body, grounding)
