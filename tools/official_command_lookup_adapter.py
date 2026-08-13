#!/usr/bin/env python3
"""Official command lookup adapter — official-source candidate integration.

Phase L.31X: This module implements the first source-quality and confidence
pipeline for official command lookup candidates.  Live lookup remains behind an
explicit enable gate and all results remain candidate-only; this adapter never
mutates a letter payload.

The default runtime is safe: when ``SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP`` is
not enabled, :func:`official_command_lookup` returns ``None``.  Tests and future
integrations may inject a deterministic search provider with
:func:`set_official_command_search_provider`.
"""

from __future__ import annotations

import inspect
import os
from typing import Any, Callable, Iterable
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Source-tier constants
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

CONFIDENCE_PROPOSE_THRESHOLD = 0.85
CONFIDENCE_WARN_THRESHOLD = 0.70
_ENABLE_ENV = "SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP"

SearchProvider = Callable[[str, str, dict[str, Any]], Iterable[dict[str, Any]]]
_SEARCH_PROVIDER: SearchProvider | None = None
_CACHE: dict[tuple[str, str], dict[str, Any] | None] = {}


# ---------------------------------------------------------------------------
# Test/future-integration hooks
# ---------------------------------------------------------------------------
def set_official_command_search_provider(provider: SearchProvider | None) -> None:
    """Inject a deterministic search provider for tests or future live search.

    The provider must return iterable result dictionaries.  This adapter will
    still enforce enablement, source tier rules, confidence gates, conflict
    handling, candidate-only output, and To-line letterhead stripping.
    """

    global _SEARCH_PROVIDER
    _SEARCH_PROVIDER = provider
    reset_official_command_lookup_cache()


def reset_official_command_lookup_cache() -> None:
    """Clear the tiny in-memory per-process lookup cache."""

    _CACHE.clear()


def official_lookup_enabled(state: dict[str, Any] | None = None) -> bool:
    """Return True only when official command lookup is explicitly enabled."""

    if isinstance(state, dict) and state.get("enable_official_command_lookup") is True:
        return True
    value = os.getenv(_ENABLE_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Source/result qualification
# ---------------------------------------------------------------------------
def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    return _clean(value).lower()


def _dict_values_match(text: str, data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    target = _norm(text)
    for key, value in data.items():
        if _norm(key) == target:
            return True
        if isinstance(value, str) and _norm(value) == target:
            return True
        if isinstance(value, dict) and any(_norm(v) == target for v in value.values()):
            return True
    return False


def _matches_existing_controlled_alias(text: str, state: dict[str, Any]) -> bool:
    """Return True when text is already a controlled alias expansion.

    Hermes expands controlled aliases before this adapter sees them.  To keep
    controlled aliases from invoking live lookup, this helper checks any alias
    maps explicitly provided in state and, when called from Hermes, the caller's
    existing controlled-alias globals.  This mirrors the accepted alias table;
    it does not create or maintain a new command database.
    """

    for key in ("controlled_aliases", "unit_aliases", "letterhead_by_from"):
        if _dict_values_match(text, state.get(key)):
            return True

    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    depth = 0
    while frame is not None and depth < 8:
        globs = frame.f_globals
        if _dict_values_match(text, globs.get("_UNIT_ALIASES")):
            return True
        if _dict_values_match(text, globs.get("_LETTERHEAD_BY_FROM")):
            return True
        frame = frame.f_back
        depth += 1
    return False


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _is_official_url(url: str) -> bool:
    host = _host(url)
    if not host:
        return False
    if host.endswith(".mil"):
        return True
    return any(
        token in host
        for token in (
            "navy.mil",
            "marines.mil",
            "usmc.mil",
            "defense.gov",
            "dod.mil",
        )
    )


def _source_tier(result: dict[str, Any]) -> str:
    tier = str(result.get("source_tier") or "").strip()
    if tier in _VALID_SOURCE_TIERS:
        return tier
    url = str(result.get("source_url") or result.get("url") or "")
    return SOURCE_TIER_OFFICIAL_LIVE if _is_official_url(url) else SOURCE_TIER_UNRESOLVED


def _confidence(result: dict[str, Any]) -> float:
    try:
        value = float(result.get("confidence", 0.0))
    except Exception:
        value = 0.0
    return max(0.0, min(1.0, value))


def _resolved_value(result: dict[str, Any], role: str) -> dict[str, Any]:
    rv = result.get("resolved_value")
    if isinstance(rv, dict):
        resolved = dict(rv)
    else:
        line = _clean(result.get(role) or result.get("candidate_full_line") or result.get("resolved_line"))
        resolved = {role: line} if line else {}

    if role != "from":
        for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address"):
            resolved.pop(key, None)
    elif not (
        resolved.get("letterhead_top_line")
        and resolved.get("letterhead_activity")
        and resolved.get("letterhead_address")
    ):
        for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address"):
            resolved.pop(key, None)
    return {k: v for k, v in resolved.items() if v}


def _candidate_from_result(command_text: str, role: str, result: dict[str, Any]) -> dict[str, Any] | None:
    tier = _source_tier(result)
    confidence = _confidence(result)
    url = _clean(result.get("source_url") or result.get("url"))
    title = _clean(result.get("source_title") or result.get("title"))
    resolved = _resolved_value(result, role)

    if tier not in {SOURCE_TIER_OFFICIAL_LIVE, SOURCE_TIER_OFFICIAL_ARCHIVED}:
        return None
    if confidence < CONFIDENCE_WARN_THRESHOLD:
        return None
    if confidence < CONFIDENCE_PROPOSE_THRESHOLD and tier != SOURCE_TIER_OFFICIAL_LIVE:
        return None
    if not url or not title or not resolved.get(role):
        return None
    if tier == SOURCE_TIER_OFFICIAL_LIVE and not _is_official_url(url):
        return None

    return {
        "candidate_type": result.get("candidate_type") or "command_expansion",
        "input_text": _clean(command_text),
        "field": role,
        "resolved_value": resolved,
        "source_tier": tier,
        "source_title": title,
        "source_url": url,
        "source_limitation": _clean(result.get("source_limitation")) or "Official-source candidate; user confirmation required before applying.",
        "confidence": confidence,
        "requires_user_confirmation": True,
    }


def _pick_single_candidate(command_text: str, role: str, results: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [c for item in results if isinstance(item, dict) for c in [_candidate_from_result(command_text, role, item)] if c]
    if not candidates:
        return None

    candidates.sort(key=lambda c: (c.get("source_tier") == SOURCE_TIER_OFFICIAL_LIVE, float(c.get("confidence", 0.0))), reverse=True)
    best = candidates[0]
    best_line = _clean((best.get("resolved_value") or {}).get(role)).lower()

    for other in candidates[1:]:
        other_line = _clean((other.get("resolved_value") or {}).get(role)).lower()
        if other_line and other_line != best_line:
            return None
    return best


def _provider_results(command_text: str, role: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    if _SEARCH_PROVIDER is None:
        return []
    try:
        return [dict(item) for item in (_SEARCH_PROVIDER(command_text, role, state) or []) if isinstance(item, dict)]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Public adapter
# ---------------------------------------------------------------------------
def official_command_lookup(
    command_text: str,
    role: str,
    state: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return an official-source command candidate or ``None``.

    The adapter performs no payload mutation.  It returns a candidate only when
    explicit enablement is present, the source is official enough, confidence
    passes the gate, and there is no conflicting official result.
    """

    text = _clean(command_text)
    field = _clean(role).lower()
    if field not in {"from", "to"} or not text:
        return None
    ctx: dict[str, Any] = state if isinstance(state, dict) else {}
    if not official_lookup_enabled(ctx):
        return None
    if _matches_existing_controlled_alias(text, ctx):
        return None

    cache_key = (field, text.lower())
    if cache_key in _CACHE:
        cached = _CACHE[cache_key]
        return dict(cached) if isinstance(cached, dict) else None

    candidate = _pick_single_candidate(text, field, _provider_results(text, field, ctx))
    _CACHE[cache_key] = dict(candidate) if isinstance(candidate, dict) else None
    return candidate
