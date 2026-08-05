#!/usr/bin/env python3
"""Nonblocking SSIC resolver for Hermes chat intake.

The resolver is intentionally lightweight and deterministic.  It provides a
reasonable assisted default when the user does not know the SSIC, while keeping
SSIC nonblocking if no confident mapping is found.
"""

from __future__ import annotations

import re
from typing import Any


SSIC_TABLE: dict[str, str] = {
    "1000": "Military Personnel",
    "1200": "Civilian Personnel",
    "1500": "Training and Education",
    "1520": "Cybersecurity / Information Assurance",
    "1590": "Safety / Mishap Investigation",
    "1650": "Awards",
    "3000": "Logistics",
    "3500": "Operations and Exercises",
    "4000": "Logistics",
    "5000": "General Administration and Management",
    "5200": "Management Programs and Inspections",
    "5210": "Records Management",
    "5216": "Official Correspondence",
    "5239": "Information Security",
    "5400": "Organization and Functions",
    "5500": "Security and Law Enforcement",
    "5600": "Public Affairs and Community Relations",
    "6000": "Medicine and Dentistry",
    "7000": "Financial Management",
    "8000": "Ordnance Material",
    "11000": "Facilities and Activities Ashore",
    "13000": "Aeronautical Material",
    "16000": "Research, Development, Test, and Evaluation",
}

_KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("5216", ("correspondence", "letter", "memo", "memorandum", "routing", "procedures", "review procedures")),
    ("1520", ("cyber", "cybersecurity", "information assurance", "network security")),
    ("1590", ("safety", "mishap", "accident", "hazard", "risk management")),
    ("1650", ("award", "commendation", "medal", "meritorious")),
    ("1500", ("training", "qualification", "course", "education", "instruction")),
    ("5200", ("inspection", "audit", "program review", "management review")),
    ("5210", ("records", "record management", "files", "disposition")),
    ("5239", ("information security", "classified", "classification")),
    ("5500", ("security", "law enforcement", "physical security", "access control")),
    ("7000", ("budget", "funding", "finance", "financial")),
    ("6000", ("medical", "health", "dental", "treatment")),
    ("5400", ("organization", "realignment", "activation", "mission and functions")),
    ("3000", ("logistics", "supply", "maintenance", "material readiness")),
    ("3500", ("operations", "exercise", "deployment", "readiness")),
]


def _normalize_text(*parts: Any) -> str:
    text = " ".join(str(part or "") for part in parts)
    return re.sub(r"\s+", " ", text).strip().lower()


def resolve_ssic(subject: str, body_text: str = "") -> dict[str, str] | None:
    """Return an inferred SSIC mapping or None if no rule matches.

    The function returns a dictionary so callers can preserve code,
    description, and source without requiring the user to know any internal
    field names.
    """

    haystack = _normalize_text(subject, body_text)
    if not haystack:
        return None

    for code, keywords in _KEYWORD_RULES:
        for keyword in keywords:
            if keyword in haystack:
                return {
                    "code": code,
                    "description": SSIC_TABLE.get(code, "Unknown"),
                    "source": "keyword",
                    "keyword": keyword,
                }
    return None


if __name__ == "__main__":
    samples = [
        "Review of correspondence procedures",
        "Cybersecurity incident response",
        "Training qualification request",
    ]
    for sample in samples:
        print(sample, "->", resolve_ssic(sample))
