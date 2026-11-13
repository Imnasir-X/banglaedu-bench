"""Prompt templates. Versioned: change PROMPT_VERSION whenever the text changes.

The role follows the item's class band and subject, so a class 5 item is not
asked as an SSC physics student and a college accounting item is asked as HSC.
"""

from __future__ import annotations

import hashlib

from .curriculum import describe

PROMPT_VERSION = "prompt-v0.2"

BAND_ROLE = {
    "primary": "তুমি বাংলাদেশের পঞ্চম শ্রেণির একজন শিক্ষার্থী।",
    "junior": "তুমি বাংলাদেশের ষষ্ঠ থেকে অষ্টম শ্রেণির একজন শিক্ষার্থী।",
    "ssc": "তুমি বাংলাদেশের নবম-দশম শ্রেণির (এসএসসি) একজন শিক্ষার্থী।",
    "hsc": "তুমি বাংলাদেশের একাদশ-দ্বাদশ শ্রেণির কলেজ (এইচএসসি) একজন শিক্ষার্থী।",
}

CLOSING_BN = (
    "প্রশ্নের উত্তর বাংলায় দাও। প্রয়োজনে সংক্ষেপে হিসাব দেখাও। "
    "উত্তরের শেষ লাইনে অবশ্যই 'উত্তর: ' লিখে চূড়ান্ত উত্তর দেবে।"
)
CLOSING_EN = (
    "Answer in English. Show brief working when the question needs it. "
    "The last line must be 'Answer: ' followed by the final answer."
)

MCQ_BN = "নিচের বহুনির্বাচনি প্রশ্নের সঠিক উত্তর বেছে নাও। শেষ লাইনে শুধু 'উত্তর: ক/খ/গ/ঘ' লেখো।"
MCQ_EN = (
    "Choose the correct option. The last line must be only 'Answer: A/B/C/D' or the Bangla letter."
)
SHORT_BN = "নিচের প্রশ্নের সংক্ষিপ্ত উত্তর দাও।"
SHORT_EN = "Answer the question briefly."
NUMERIC_BN = "নিচের প্রশ্নটি গাণিতিক। শেষ লাইনে 'উত্তর: <মান> <একক>' আকারে চূড়ান্ত মান লেখো।"
NUMERIC_EN = "This question is a calculation. The last line must be 'Answer: <value> <unit>'."
SRIJONSHIL_BN = "নিচে একটি সৃজনশীল প্রশ্নের উদ্দীপক ও একটি অংশ দেওয়া হলো। শুধু এই অংশের উত্তর দাও।"
SRIJONSHIL_EN = "A creative-question stimulus and one part follow. Answer only that part."

GROUNDING_BN = "নিচে পাঠ্যক্রমের প্রাসঙ্গিক অংশ দেওয়া হলো। প্রয়োজন হলে এটি ব্যবহার করো:\n<পাঠ্যক্রম>\n{context}\n</পাঠ্যক্রম>\n\n"
GROUNDING_EN = "Curriculum context follows. Use it only if it helps:\n<curriculum>\n{context}\n</curriculum>\n\n"

PROMPT_FINGERPRINT = hashlib.sha256(
    "\n".join(
        [
            PROMPT_VERSION,
            *BAND_ROLE.values(),
            CLOSING_BN,
            CLOSING_EN,
            MCQ_BN,
            MCQ_EN,
            SHORT_BN,
            SHORT_EN,
            NUMERIC_BN,
            NUMERIC_EN,
            SRIJONSHIL_BN,
            SRIJONSHIL_EN,
            GROUNDING_BN,
            GROUNDING_EN,
        ]
    ).encode()
).hexdigest()


def _english(item: dict) -> bool:
    return item.get("language") == "en" or item.get("subject") == "english"


def system_for(item: dict) -> str:
    info = describe(item)
    parts = [BAND_ROLE[info["class_band"]], f"বিষয়: {info['subject_bn']}."]
    if info["stream"] != "common":
        parts.append(f"বিভাগ: {info['stream_bn']}.")
    if info.get("paper"):
        parts.append(f"পত্র: {info['paper']}.")
    closing = CLOSING_EN if _english(item) else CLOSING_BN
    return " ".join(parts) + " " + closing


def _wrap(item: dict, body: str, grounding: str) -> list[dict]:
    if grounding:
        header = (GROUNDING_EN if _english(item) else GROUNDING_BN).format(context=grounding)
    else:
        header = ""
    return [
        {"role": "system", "content": system_for(item)},
        {"role": "user", "content": header + body},
    ]


def mcq_messages(item: dict, grounding: str = "") -> list[dict]:
    instr = MCQ_EN if _english(item) else MCQ_BN
    opts = "\n".join(f"({o['label']}) {o['text']}" for o in item["options"])
    return _wrap(item, f"{instr}\n\nপ্রশ্ন: {item['question']}\n{opts}", grounding)


def short_messages(item: dict, grounding: str = "") -> list[dict]:
    english = _english(item)
    if "numeric" in item["answer_key"]:
        instr = NUMERIC_EN if english else NUMERIC_BN
    else:
        instr = SHORT_EN if english else SHORT_BN
    return _wrap(item, f"{instr}\n\nপ্রশ্ন: {item['question']}", grounding)


def srijonshil_messages(item: dict, part: dict, grounding: str = "") -> list[dict]:
    english = _english(item)
    instr = SRIJONSHIL_EN if english else SRIJONSHIL_BN
    if "numeric" in part["answer_key"]:
        instr += " " + (NUMERIC_EN if english else "শেষ লাইনে 'উত্তর: <মান> <একক>' আকারে চূড়ান্ত মান লেখো।")
    body = f"{instr}\n\nউদ্দীপক: {item['question']}\n\n({part['label']}) {part['question']}"
    return _wrap(item, body, grounding)
