"""Text normalisation helpers for Bangla and mixed Bangla/English model output."""

from __future__ import annotations

import re
import unicodedata

BN_DIGITS = "০১২৩৪৫৬৭৮৯"
_BN_TO_ASCII = str.maketrans(BN_DIGITS, "0123456789")
_ASCII_TO_BN = str.maketrans("0123456789", BN_DIGITS)

# Option labels. Index 0..3 maps across all scripts.
BN_LABELS = ("ক", "খ", "গ", "ঘ")
EN_LABELS = ("A", "B", "C", "D")
BN_NUM_LABELS = ("১", "২", "৩", "৪")
NUM_LABELS = ("1", "2", "3", "4")

# Zero-width joiner/non-joiner and other invisible characters that models emit
# inconsistently. They are removed only for comparison, never from stored data.
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)

# Bangla danda, double danda, and common ASCII/Unicode punctuation.
_PUNCT_RE = re.compile(r"[\u0964\u0965!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~“”‘’…–—]")
_WS_RE = re.compile(r"\s+")


def bn_to_ascii_digits(text: str) -> str:
    """Convert Bangla digits (০-৯) to ASCII digits."""
    return text.translate(_BN_TO_ASCII)


def ascii_to_bn_digits(text: str) -> str:
    """Convert ASCII digits to Bangla digits."""
    return text.translate(_ASCII_TO_BN)


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def normalize_text(text: str) -> str:
    """Normalise a short answer for comparison.

    NFC, digits to ASCII, invisible characters removed, punctuation (including
    the Bangla danda) removed, whitespace collapsed, ASCII lower-cased.
    """
    text = nfc(text).translate(_INVISIBLE)
    text = bn_to_ascii_digits(text)
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text.lower()


def label_index(label: str) -> int | None:
    """Return 0-3 for any recognised option label (ক/A/1/১, any case), else None."""
    label = label.strip()
    for labels in (BN_LABELS, EN_LABELS, BN_NUM_LABELS, NUM_LABELS):
        if label in labels:
            return labels.index(label)
    if label.upper() in EN_LABELS:
        return EN_LABELS.index(label.upper())
    return None
