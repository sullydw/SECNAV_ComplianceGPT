#!/usr/bin/env python3
"""Official command lookup adapter — skeleton for future live lookup.

Phase L.31W: This module defines the stable adapter interface that future
live online lookup will plug into.  It performs no internet searches, no
broad guessing, and no payload mutation.  The default implementation always
returns None.

When implemented later, the adapter may return a candidate dict with:
    candidate_type, resolved_value, source_tier, source_title, source_url,
    source_limitation, confidence, requires_user_confirmation

Accepted source tiers:
    official_live, official_archived, secondary_credible, user_provided,
    unresolved

Confidence gates (documentation only — not enforced by the skeleton):
    confidence >= 0.85  → may propose candidate
    confidence 0.70–0.84 → may propose with caution/warning
    confidence < 0.70   → do not propose; preserve literal
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Source-tier constants (documented contract for future phases)
# ---------------------------------------------------------------------------
SOURCE_TIER_OFFICIAL_LIVE = "official_live"
SOURCE_TIER_OFFICIAL_ARCHIVED = "official_archived"
SOURCE_TIER_SECONDARY_CREDIBLE = "secondary_credible"
SOURCE_TIER_USER_PROVIDED = "user_provided"
SOURCE_TIER_UNRESOLVED = "unresolved"

_VALID_SOURCE_TIERS: frozenset[str] = frozenset(
    {
        SOURCE_TIER_OFFICIAL_LIVE,
        SOURCE_TIER_OFFICIAL_ARCHIVED,
        SOURCE_TIER_SECONDARY_CREDIBLE,
        SOURCE_TIER_USER_PROVIDED,
        SOURCE_TIER_UNRESOLVED,
    }
)

# ---------------------------------------------------------------------------
# Confidence-gate documentation (not enforced by the skeleton)
# ---------------------------------------------------------------------------
CONFIDENCE_PROPOSE_THRESHOLD = 0.85
CONFIDENCE_WARN_THRESHOLD = 0.70


def official_command_lookup(
    command_text: str,
    role: str,
    state: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Look up an official command/unit from live sources.

    **Skeleton (L.31W):** Always returns None.  No internet lookup, no
    guessing, no payload mutation, no static command database.

    When implemented in a future phase this function may return a candidate
    dict shaped like::

        {
            "candidate_type": "command_expansion",
            "resolved_value": {
                "from": "Commanding Officer, Example Command",
                "letterhead_top_line": "DEPARTMENT OF THE NAVY",
                "letterhead_activity": "EXAMPLE COMMAND",
                "letterhead_address": "NORFOLK VA 23511-0000",
            },
            "source_tier": "official_live",
            "source_title": "Example Command Official Homepage",
            "source_url": "https://www.example.navy.mil/",
            "source_limitation": "Official page reviewed; verify currency.",
            "confidence": 0.86,
            "requires_user_confirmation": True,
        }

    Args:
        command_text: The unresolved literal command phrase from the user.
        role: The field context, normally ``"from"`` or ``"to"``.
        state: Current chat/session context including rejected-candidate
               memory.

    Returns:
        ``None`` (skeleton).  Future phases may return a candidate dict or
        ``None`` when no reliable result is found.
    """
    # L.31W skeleton — no live lookup, no static database, no mutation.
    _ = (command_text, role, state)
    return None
