import pytest

from banglaedu_bench.normalize import (
    ascii_to_bn_digits,
    bn_to_ascii_digits,
    label_index,
    normalize_text,
)
from banglaedu_bench.scoring import (
    extract_numbers,
    numeric_match,
    parse_mcq,
    parse_numeric,
    text_match,
)

OPTS = [
    {"label": "ক", "text": "৬০ cm"},
    {"label": "খ", "text": "৩০ cm"},
    {"label": "গ", "text": "১৫ cm"},
    {"label": "ঘ", "text": "৭.৫ cm"},
]


def test_digits_roundtrip():
    assert bn_to_ascii_digits("১২৩.৪৫") == "123.45"
    assert ascii_to_bn_digits("2026") == "২০২৬"


def test_label_index_all_scripts():
    assert [label_index(x) for x in ("ক", "B", "c", "৩", "4")] == [0, 1, 2, 2, 3]
    assert label_index("ঙ") is None


def test_normalize_text_strips_danda_and_zw():
    assert normalize_text("জড়তা।") == normalize_text("জড়\u200cতা")
    assert normalize_text("  ব্যারোমিটার। ") == "ব্যারোমিটার"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("উত্তর: খ", "খ"),
        ("সঠিক উত্তর হলো (গ)", "গ"),
        ("Answer: C", "গ"),
        ("The answer is B.", "খ"),
        ("answer: 4", "ঘ"),
        ("উত্তর: ৩", "গ"),
        ("খ", "খ"),
        ("(ঘ)", "ঘ"),
        ("হিসাব করে পাই f = r/2।\nগ) ১৫ cm", "গ"),
        ("f = r/2 = ১৫ cm", "গ"),  # option-text fallback
        ("প্রথমে ক ও খ বাদ দিই, তারপর... উত্তর: ঘ", "ঘ"),  # marker beats mentions
    ],
)
def test_parse_mcq(text, expected):
    assert parse_mcq(text, OPTS) == expected


@pytest.mark.parametrize("text", ["", "কলম", "আমি নিশ্চিত নই", "ক অথবা খ হতে পারে"])
def test_parse_mcq_unparseable(text):
    assert parse_mcq(text, None) is None


def test_bangla_word_letters_are_not_labels():
    # "কম" starts with ক but is a word, not an option label.
    assert parse_mcq("চাপ কম হয়", None) is None


def test_extract_numbers_formats():
    assert extract_numbers("২ m s⁻²") == [2.0]
    assert extract_numbers("৩ × ১০⁸ m s⁻¹") == [3e8]
    assert extract_numbers("4,20,000 J") == [420000.0]
    assert extract_numbers("9e-3 N") == [pytest.approx(9e-3)]
    assert extract_numbers("৯ × ১০^-৩ N") == [pytest.approx(9e-3)]
    assert extract_numbers("১/৮ অংশ") == [0.125]
    assert extract_numbers("-5 এবং 3.5") == [-5.0, 3.5]


def test_english_answer_is_not_cut_at_ans_inside_a_word():
    key = {"text": "hypertext transfer protocol", "aliases": ["Hypertext Transfer Protocol"]}
    assert text_match("উত্তর: hypertext transfer protocol", key)


def test_parse_numeric_prefers_marker():
    assert parse_numeric("h = ½gt² = ½ × 9.8 × 3²\nউত্তর: ৪৪.১ m") == pytest.approx(44.1)
    assert parse_numeric("প্রথমে 2 আর 3 যোগ করি; ফল 5") == 5.0
    assert parse_numeric("জানি না") is None


def test_numeric_match_tolerance_and_alt():
    key = {"value": 16.6667, "rel_tol": 0.01, "abs_tol": 0}
    assert numeric_match(16.67, key)
    assert not numeric_match(16.0, key)
    key2 = {"value": 2.0, "rel_tol": 0.01, "alt_values": [-2.0]}
    assert numeric_match(-2.0, key2)
