from __future__ import annotations

from dataclasses import dataclass

from app.services.scanner import scan_contract_text


@dataclass
class FakePattern:
    pattern: str
    is_regex: bool


@dataclass
class FakeClauseType:
    id: int
    patterns: list[FakePattern]


def test_keyword_match_is_case_insensitive():
    clause_types = [
        FakeClauseType(
            id=1,
            patterns=[FakePattern(pattern="termination", is_regex=False)],
        )
    ]
    text = "This contract includes a TERMINATION clause."
    results = scan_contract_text(text, clause_types)
    assert results == [results[0]] 
    assert results[0].clause_type_id == 1
    assert results[0].detected is True


def test_keyword_no_match():
    clause_types = [
        FakeClauseType(
            id=1,
            patterns=[FakePattern(pattern="limitation of liability", is_regex=False)],
        )
    ]
    text = "This contract includes a termination clause."
    results = scan_contract_text(text, clause_types)
    assert results[0].detected is False


def test_regex_match_is_case_insensitive():
    clause_types = [
        FakeClauseType(
            id=1,
            patterns=[FakePattern(pattern=r"terminate\s+this\s+agreement", is_regex=True)],
        )
    ]
    text = "We may TERMINATE this agreement at any time."
    results = scan_contract_text(text, clause_types)
    assert results[0].detected is True


def test_empty_patterns_is_false():
    clause_types = [FakeClauseType(id=1, patterns=[])]
    text = "anything at all"
    results = scan_contract_text(text, clause_types)
    assert results[0].detected is False
