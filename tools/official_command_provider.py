#!/usr/bin/env python3
"""Official command provider — deterministic fixture and live provider interface.

Phase L.32B: This module defines the provider contract from L.32A and
implements a deterministic fixture provider for smoke tests.  No real
internet lookup is performed by this module.

The provider callable contract is:

    provider(command_text: str, role: str, state: dict[str, Any]) -> Iterable[dict[str, Any]]

Allowed roles: ``"from"``, ``"to"``.  Invalid roles return an empty iterable.
The provider is a pure data source — it never mutates state, never applies
fields, and never bypasses the confirmation gate.
"""

from __future__ import annotations

import re
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class OfficialCommandProviderError(Exception):
    """Base exception for official command provider errors."""


# ---------------------------------------------------------------------------
# SourceResult — documented dict shape (not enforced at runtime)
# ---------------------------------------------------------------------------
# A SourceResult dict has these keys:
#
#   resolved_value   dict[str, str]   Required.  Must include "from" or "to".
#   source_tier       str              Required.  One of the accepted tiers.
#   source_title      str              Required.  Human-readable source label.
#   source_url        str              Required.  URL of the source page.
#   confidence        float            Required.  0.0–1.0 confidence score.
#
# Optional keys:
#   source_limitation str              Explanation of why confirmation is needed.
#   candidate_type    str              Defaults to "command_expansion".
#
# For From candidates, resolved_value may optionally include:
#   letterhead_top_line, letterhead_activity, letterhead_address
#
# For To candidates, those letterhead fields are forbidden.


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------
def _norm(text: str) -> str:
    """Normalize text for fixture lookup: lowercase, trim, collapse whitespace."""
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


# ---------------------------------------------------------------------------
# OfficialCommandProvider — abstract base
# ---------------------------------------------------------------------------
class OfficialCommandProvider:
    """Abstract base for official command lookup providers.

    Subclasses must implement ``__call__`` matching the provider contract.
    """

    def __call__(
        self,
        command_text: str,
        role: str,
        state: dict[str, Any],
    ) -> Iterable[dict[str, Any]]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# FixtureOfficialCommandProvider
# ---------------------------------------------------------------------------
class FixtureOfficialCommandProvider(OfficialCommandProvider):
    """Deterministic fixture provider for smoke tests.

    Constructed with an explicit list of fixture dicts.  Performs no web
    calls, no filesystem search, and contains no static command database.

    Fixture entries are dicts like::

        {
            "input_text": "Naval Example Command",
            "role": "from",
            "resolved_value": {
                "from": "Commanding Officer, Naval Example Command",
                "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                "letterhead_activity": "NAVAL EXAMPLE COMMAND",
                "letterhead_address": "NORFOLK VA 23511-0000",
            },
            "source_tier": "official_live",
            "source_title": "Naval Example Command Official .mil Page",
            "source_url": "https://www.example.navy.mil/naval-example-command",
            "confidence": 0.92,
        }

    Lookup normalizes ``command_text`` (lowercase, trim, collapse spaces) and
    matches against ``input_text`` + ``role``.  Multiple fixtures for the same
    ``input_text`` + ``role`` are returned in insertion order.
    """

    def __init__(self, fixtures: list[dict[str, Any]] | None = None) -> None:
        self._fixtures: list[dict[str, Any]] = list(fixtures or [])

    def __call__(
        self,
        command_text: str,
        role: str,
        state: dict[str, Any],
    ) -> Iterable[dict[str, Any]]:
        """Return matching fixture results for *command_text* and *role*.

        *state* is accepted for contract compatibility but ignored.
        """
        role_key = _norm(role)
        if role_key not in {"from", "to"}:
            return []

        text_key = _norm(command_text)
        if not text_key:
            return []

        results: list[dict[str, Any]] = []
        for fixture in self._fixtures:
            if not isinstance(fixture, dict):
                continue
            if _norm(fixture.get("input_text", "")) == text_key and _norm(fixture.get("role", "")) == role_key:
                # Return a shallow copy so callers can't mutate our fixtures
                results.append(dict(fixture))
        return results


# ---------------------------------------------------------------------------
# build_fixture_provider
# ---------------------------------------------------------------------------
def build_fixture_provider(
    fixtures: list[dict[str, Any]] | None = None,
) -> FixtureOfficialCommandProvider:
    """Create a :class:`FixtureOfficialCommandProvider` from *fixtures*.

    If *fixtures* is ``None``, the provider starts with an empty fixture list
    (all lookups return ``[]``).
    """
    return FixtureOfficialCommandProvider(fixtures)
