from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable



REGEX_FLAGS = re.IGNORECASE


@dataclass(frozen=True)
class ScanResult:
    clause_type_id: int
    detected: bool


def _detect_clause(contract_text: str, patterns) -> bool:
    """
    Return True if any pattern matches the contract text.

    patterns: iterable of objects with attributes:
      - pattern: str
      - is_regex: bool
    """
    hay_lower = contract_text.lower()
    for p in patterns:
        if p.is_regex:
            if re.search(p.pattern, contract_text, flags=REGEX_FLAGS):
                return True
        else:
            if p.pattern.lower() in hay_lower:
                return True
    return False


def scan_contract_text(contract_text: str, clause_types: Iterable) -> list[ScanResult]:
    """
    Scan contract text against a list of clause types.

    clause_types: iterable of objects with:
      - id: int
      - patterns: iterable (each has pattern/is_regex)
    """
    results: list[ScanResult] = []
    for ct in clause_types:
        detected = _detect_clause(contract_text, ct.patterns) if ct.patterns else False
        results.append(ScanResult(clause_type_id=ct.id, detected=detected))
    return results
