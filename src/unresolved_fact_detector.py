#!/usr/bin/env python3
"""
Unresolved Fact Detector — Phase L.29L Prototype

Deterministic unresolved-fact detector that reads the rule-to-fact mapping
and emits UNRESOLVED_FACTS_V1 JSON from a payload and optional user text.

No live lookups.
No candidate creation.
No LLM calls.
No network calls.
No file writes.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

DEFAULT_MAPPING_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "rules_v6", "CCI", "cci_unresolved_fact_map.json"
)


def _is_unresolved(value: Any) -> bool:
    """Return True if a payload value is considered absent/blank/unresolved."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict) and len(value) == 0:
        return True
    return False


def _load_mapping(mapping_path: str | None = None) -> dict:
    path = mapping_path or DEFAULT_MAPPING_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _determine_doc_type(
    payload: dict,
    doc_type: str | None = None,
) -> str:
    if doc_type is not None:
        return doc_type
    payload_dt = payload.get("doc_type") if isinstance(payload, dict) else None
    if payload_dt is not None:
        return str(payload_dt)
    return "standard_letter"


def _subject_formatting_facts(
    payload: dict,
    applicable_mappings: list[dict],
) -> list[dict]:
    """
    Emit formatting-related facts for subject text when present.
    Conservative: only emit when the subject exists but violates a formatting
    rule that the mapping supports. Never mutate the payload.
    """
    subj = payload.get("subj")
    if _is_unresolved(subj):
        return []
    if not isinstance(subj, str):
        return []

    facts = []
    for m in applicable_mappings:
        rid = m.get("rule_id", "")
        if rid == "CCI-CH7-SUBJ-002" and subj:
            # Terminal punctuation check
            if subj[-1] in ".?!":
                facts.append(_make_fact(m, subj, "subject ends with terminal punctuation", priority_override="recommended"))
        elif rid == "CCI-CH7-SUBJ-001" and subj:
            # ALL CAPS check (applies to letters only; memos are sentence-case)
            doc_types = m.get("doc_types", [])
            letter_types = {"standard_letter", "multiple_address_letter", "endorsement", "joint_letter"}
            if any(dt in letter_types for dt in doc_types):
                if not subj.isupper():
                    facts.append(_make_fact(m, subj, "subject is not all caps for letter type", priority_override="recommended"))
        elif rid == "CCI-CH7-SUBJ-005" and subj:
            # Vague subject: <= 2 words is a safer conservative threshold
            word_count = len(subj.split())
            if word_count <= 2:
                facts.append(_make_fact(m, subj, f"subject is vague ({word_count} words)", priority_override="recommended"))
        elif rid == "CCI-CH7-SUBJ-006" and subj:
            # Acronym detection: be conservative.
            # For all-caps letter subjects, only flag very short uppercase tokens (2-4 chars)
            # that look like abbreviations; exclude common short words.
            # For mixed-case subjects, any embedded uppercase sequence of 2+ is flagged.
            if subj.isupper():
                tokens = re.findall(r"\b[A-Z]{2,4}\b", subj)
                common_short = {
                    "THE", "AND", "FOR", "FROM", "TO", "OF", "IN", "ON", "AT", "BY", "WITH",
                    "CO", "LT", "JR", "SR", "II", "III", "IV", "VIA", "C/O"
                }
                potential = [t for t in tokens if t not in common_short]
                if potential:
                    facts.append(_make_fact(m, subj, f"subject contains potential acronyms: {', '.join(potential)}", priority_override="recommended"))
            else:
                if re.search(r"[A-Z]{2,}", subj):
                    facts.append(_make_fact(m, subj, "subject contains acronyms", priority_override="recommended"))
    return facts


def _user_text_facts(
    payload: dict,
    user_text: str | None,
    applicable_mappings: list[dict],
) -> list[dict]:
    """
    Surface facts from user_text only where rules/mapping already support them.
    Conservative. No invented expansions.
    """
    if not user_text:
        return []
    text = user_text.strip()
    if not text:
        return []

    facts = []
    lower = text.lower()

    for m in applicable_mappings:
        field = m.get("field")
        rid = m.get("rule_id", "")

        # SSIC ignorance
        if field == "ssic" and "ssic" in lower and ("dont know" in lower or "don't know" in lower or "unknown" in lower or "unsure" in lower or "no ssic" in lower):
            # Only emit if field is actually unresolved
            if _is_unresolved(payload.get("ssic")):
                facts.append(_make_fact(m, None, "user explicitly stated they do not know the SSIC"))

        # Vague date
        if field == "date" and _is_unresolved(payload.get("date")):
            vague_date_phrases = ["next month", "tbd", "open date", "later", "to be determined", "soon", "pending"]
            if any(phrase in lower for phrase in vague_date_phrases):
                facts.append(_make_fact(m, None, "user text contains vague date phrase"))

        # Copy-to hint
        if field in ("copy_to", "copy to") and _is_unresolved(payload.get("copy_to")):
            copy_hint_phrases = ["copy ", "cc ", "c.c. ", "copied to", "also send to"]
            if any(phrase in lower for phrase in copy_hint_phrases):
                facts.append(_make_fact(m, None, "user text hints at copy-to recipients"))

        # Unknown acronyms in user text (only if mapping supports live_lookup/ask_user for a relevant field)
        if field in ("from", "to", "body") and m.get("recommended_action") in ("live_lookup_or_ask_user", "ask_user"):
            raw_acronyms = re.findall(r"\b[A-Z]{2,6}\b", text)
            # Filter common stop-words / very short words that are not acronyms
            stop_words = {"THE", "AND", "FOR", "FROM", "TO", "OF", "IN", "ON", "AT", "BY", "WITH", "A", "AN", "CO", "LT", "JR", "SR", "II", "III", "IV", "DR", "MR", "MRS", "MS"}
            acronyms = [a for a in raw_acronyms if a not in stop_words and len(a) >= 2]
            if acronyms and _is_unresolved(payload.get(field)):
                facts.append(_make_fact(m, None, f"user text contains possible acronyms in {field} context: {', '.join(acronyms[:5])}"))

    return facts


def _make_fact(mapping: dict, input_text: Any, reason_detail: str, priority_override: str | None = None) -> dict:
    return {
        "fact_id": f"fact_{mapping['mapping_id']}",
        "rule_id": mapping.get("rule_id", ""),
        "mapping_id": mapping.get("mapping_id", ""),
        "source_file": mapping.get("source_file", ""),
        "category": mapping.get("fact_category", ""),
        "field": mapping.get("field", ""),
        "input_text": input_text if input_text is not None else None,
        "status": "unresolved",
        "priority": priority_override if priority_override else mapping.get("priority", "recommended"),
        "recommended_action": mapping.get("recommended_action", "ask_user"),
        "candidate_type": mapping.get("candidate_type"),
        "question": mapping.get("question_template", ""),
        "reason": reason_detail,
        "evidence": mapping.get("evidence", {}),
    }


def detect_unresolved_facts(
    payload: dict,
    user_text: str | None = None,
    doc_type: str | None = None,
    mapping_path: str | None = None,
) -> dict:
    """
    Detect unresolved facts for a BuilderSession payload.

    Args:
        payload: Current builder payload dict.
        user_text: Optional raw user message text for assisted detection.
        doc_type: Optional override. Falls back to payload["doc_type"], then "standard_letter".
        mapping_path: Optional override path to cci_unresolved_fact_map.json.

    Returns:
        UNRESOLVED_FACTS_V1 dict with traceable rule IDs, no mutations to payload.
    """
    mapping_data = _load_mapping(mapping_path)
    selected_doc_type = _determine_doc_type(payload, doc_type)

    # Filter mappings applicable to this doc_type
    applicable = []
    for m in mapping_data.get("mappings", []):
        if selected_doc_type in m.get("doc_types", []):
            applicable.append(m)

    # Deduplicate by rule_id for deterministic output
    seen_rule_fields = set()
    facts = []

    for m in applicable:
        field = m.get("field")
        rule_id = m.get("rule_id", "")
        key = (rule_id, field)
        if key in seen_rule_fields:
            continue
        seen_rule_fields.add(key)

        # Determine if the field is unresolved
        if field:
            value = payload.get(field)
            if _is_unresolved(value):
                facts.append(_make_fact(m, value, f"{field} is unresolved for doc_type={selected_doc_type}"))

    # Subject formatting facts (only when subject is present but malformed)
    facts.extend(_subject_formatting_facts(payload, applicable))

    # User-text assisted facts
    facts.extend(_user_text_facts(payload, user_text, applicable))

    # Sort deterministically: blocking first, then recommended, then optional
    priority_order = {"blocking": 0, "recommended": 1, "optional": 2}
    facts.sort(key=lambda f: (priority_order.get(f["priority"], 99), f["rule_id"], f["field"]))

    # Re-number fact_ids deterministically
    for idx, fact in enumerate(facts, start=1):
        fact["fact_id"] = f"fact_{idx:03d}"

    summary = {
        "blocking": sum(1 for f in facts if f["priority"] == "blocking"),
        "recommended": sum(1 for f in facts if f["priority"] == "recommended"),
        "optional": sum(1 for f in facts if f["priority"] == "optional"),
    }

    return {
        "version": "UNRESOLVED_FACTS_V1",
        "doc_type": selected_doc_type,
        "rule_profile": mapping_data.get("mapping_version", "RULE_FACT_MAP_V1"),
        "facts": facts,
        "summary": summary,
    }


if __name__ == "__main__":
    # Minimal CLI smoke test
    import sys
    test_payload = {"doc_type": "standard_letter"}
    result = detect_unresolved_facts(test_payload)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
