import re


_WHITESPACE_RE = re.compile(r"[ \t]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def normalize_text(value: str) -> str:
    cleaned = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    cleaned = _BLANK_LINES_RE.sub("\n\n", cleaned)
    return cleaned


def estimate_token_count(value: str) -> int:
    if not value:
        return 0
    return max(1, int(len(value.split()) * 1.25))
