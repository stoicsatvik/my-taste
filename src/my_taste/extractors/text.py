from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_SENTENCE_RE = re.compile(r"[.!?]+")

_CORPORATE = {
    "innovative", "innovation", "leverage", "synergy", "solutions", "transform",
    "transformation", "next-generation", "cutting-edge", "revolutionize", "seamless",
    "empower", "unlock", "robust", "dynamic", "ecosystem", "optimize",
}

_INTENSIFIERS = {
    "very", "extremely", "really", "absolutely", "massive", "insane", "crazy",
    "best", "worst", "never", "always",
}


def _ratio(n: float, d: float) -> float:
    return 0.0 if d <= 0 else n / d


def extract_text_features(text: str) -> dict[str, float]:
    """Return compact, interpretable features scaled mostly into [0, 1]."""
    raw_words = _WORD_RE.findall(text)
    words = [w.lower() for w in raw_words]
    word_count = len(words)
    sentence_count = max(1, len(_SENTENCE_RE.findall(text)))
    unique = len(set(words))

    digit_tokens = sum(any(ch.isdigit() for ch in w) for w in raw_words)
    corporate = sum(w in _CORPORATE for w in words)
    intensifiers = sum(w in _INTENSIFIERS for w in words)
    first_person = sum(w in {"i", "me", "my", "mine", "we", "our"} for w in words)
    second_person = sum(w in {"you", "your", "yours"} for w in words)
    questions = text.count("?")
    exclamations = text.count("!")
    bullets = sum(line.lstrip().startswith(("- ", "* ", "+ ")) for line in text.splitlines())
    headings = sum(line.lstrip().startswith("#") for line in text.splitlines())
    code_ticks = text.count("`")
    uppercase_words = sum(len(w) >= 2 and w.isupper() for w in raw_words)
    avg_sentence_words = word_count / sentence_count if word_count else 0.0

    return {
        "brevity": 1.0 / (1.0 + word_count / 40.0),
        "specificity": min(1.0, _ratio(digit_tokens, max(1, word_count)) * 10.0),
        "corporate_language": min(1.0, _ratio(corporate, max(1, word_count)) * 8.0),
        "intensity": min(1.0, _ratio(intensifiers + exclamations, max(1, word_count)) * 6.0),
        "first_person": min(1.0, _ratio(first_person, max(1, word_count)) * 5.0),
        "second_person": min(1.0, _ratio(second_person, max(1, word_count)) * 5.0),
        "questioning": min(1.0, questions / 3.0),
        "structured_formatting": min(1.0, (bullets + headings + code_ticks / 2.0) / 5.0),
        "uppercase_emphasis": min(1.0, _ratio(uppercase_words, max(1, word_count)) * 5.0),
        "lexical_variety": _ratio(unique, max(1, word_count)),
        "long_sentences": min(1.0, avg_sentence_words / 30.0),
    }
