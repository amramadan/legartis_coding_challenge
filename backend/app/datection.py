import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Pattern:
    text: str
    is_regex: bool

def detect(text: str, patterns: list[Pattern]) -> bool:
    hay = text.lower()
    for p in patterns:
        if p.is_regex:
            if re.search(p.text, text, flags=re.IGNORECASE | re.MULTILINE):
                return True
        else:
            if p.text.lower() in hay:
                return True
    return False