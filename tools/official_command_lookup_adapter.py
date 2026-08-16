#!/usr/bin/env python3
"""Official command lookup adapter — official-source candidate integration.

Live lookup remains behind an explicit enable gate and all results remain
candidate-only; this adapter never mutates a letter payload.  Registered
providers are normalized through the deterministic official provider source
filter before candidate construction.
"""

from __future__ import annotations

import inspect
import os
import sys
import threading
import time
from types import ModuleType
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
    """Inject a deterministic search provider for tests or future live search."""

    global _SEARCH_PROVIDER
    _SEARCH_PROVIDER = provider
    reset_official_command_lookup_cache()


def register_official_command_provider(provider: SearchProvider | None) -> None:
    """Register an official command provider with the adapter.

    Accepts ``None`` to clear the provider.  Does **not** enable live lookup by
    itself; the adapter still enforces ``SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP``.
    """

    set_official_command_search_provider(provider)


def register_fixture_official_command_provider(
    fixtures: list[dict[str, Any]] | None = None,
) -> Any:
    """Build a FixtureOfficialCommandProvider and register it."""

    from official_command_provider import build_fixture_provider  # noqa: PLC0415

    provider = build_fixture_provider(fixtures)
    set_official_command_search_provider(provider)
    return provider


def build_and_register_live_official_command_provider(
    *,
    enable_network: bool = False,
    candidate_urls: Iterable[str] | None = None,
    fetcher: Any = None,
    parser: Any = None,
    timeout_seconds: Any = None,
) -> Any:
    """Build a live provider skeleton and register it with the adapter.

    This is the explicit opt-in wiring path for the L.32F/L.32H live
    provider skeleton.  It builds the provider via
    :func:`official_command_provider.build_live_provider`, registers it with
    the adapter, and returns the provider instance.

    It does **not** enable ``SECNAV_ENABLE_OFFICIAL_COMMAND_LOOKUP``, does
    **not** perform network by default (``enable_network`` defaults to
    ``False``), does **not** contain a static command database, does **not**
    mutate Hermes state, and does **not** auto-confirm/apply candidates.  The
    adapter gate remains authoritative: with the gate unset the adapter
    returns ``None`` and the provider/fetcher is never called.
    """

    from official_command_provider import build_live_provider  # noqa: PLC0415

    provider = build_live_provider(
        enable_network=enable_network,
        candidate_urls=candidate_urls,
        fetcher=fetcher,
        parser=parser,
        timeout_seconds=timeout_seconds,
    )
    set_official_command_search_provider(provider)
    return provider


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
    """Return True when text is already a controlled alias expansion."""

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
        for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
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

    raw_rv = result.get("resolved_value")
    raw_has_full_letterhead = (
        isinstance(raw_rv, dict)
        and bool(raw_rv.get("letterhead_top_line"))
        and bool(raw_rv.get("letterhead_activity"))
        and bool(raw_rv.get("letterhead_address"))
    )

    resolved = _resolved_value(result, role)

    if tier not in {SOURCE_TIER_OFFICIAL_LIVE, SOURCE_TIER_OFFICIAL_ARCHIVED, SOURCE_TIER_USER_PROVIDED}:
        return None

    if tier == SOURCE_TIER_USER_PROVIDED:
        if not resolved.get(role):
            return None
        limitation = _clean(result.get("source_limitation")) or "User-provided source candidate; confirm before applying."
        return {
            "candidate_type": result.get("candidate_type") or "command_expansion",
            "input_text": _clean(command_text),
            "field": role,
            "resolved_value": resolved,
            "source_tier": tier,
            "source_title": title or "User-provided source",
            "source_url": url,
            "source_limitation": limitation,
            "confidence": confidence,
            "requires_user_confirmation": True,
        }

    if confidence < CONFIDENCE_WARN_THRESHOLD:
        return None
    if confidence < CONFIDENCE_PROPOSE_THRESHOLD and tier != SOURCE_TIER_OFFICIAL_LIVE:
        return None
    if not url or not title or not resolved.get(role):
        return None
    if tier == SOURCE_TIER_OFFICIAL_LIVE and not _is_official_url(url):
        return None

    limitation = _clean(result.get("source_limitation"))
    if not limitation:
        if role != "from":
            limitation = "To-line candidates do not set letterhead; confirmation mutates only the To field."
        elif not raw_has_full_letterhead:
            limitation = "Official source did not provide complete letterhead address; letterhead not proposed."
        elif tier == SOURCE_TIER_OFFICIAL_ARCHIVED:
            limitation = "Official archived source candidate; verify current validity before applying."
        else:
            limitation = "Official-source candidate; user confirmation required before applying."

    return {
        "candidate_type": result.get("candidate_type") or "command_expansion",
        "input_text": _clean(command_text),
        "field": role,
        "resolved_value": resolved,
        "source_tier": tier,
        "source_title": title,
        "source_url": url,
        "source_limitation": limitation,
        "confidence": confidence,
        "requires_user_confirmation": True,
    }


def _filter_and_rank_provider_results(
    command_text: str,
    role: str,
    raw_results: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply L.32D source filtering/ranking, failing closed on any error."""

    try:
        from official_command_provider import (  # noqa: PLC0415
            filter_provider_results,
            rank_provider_results,
        )

        filtered = filter_provider_results(raw_results, role)
        return rank_provider_results(filtered, role, command_text)
    except Exception:
        return []


def _pick_single_candidate(command_text: str, role: str, results: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [c for item in results if isinstance(item, dict) for c in [_candidate_from_result(command_text, role, item)] if c]
    if not candidates:
        return None

    official = [c for c in candidates if c.get("source_tier") in {SOURCE_TIER_OFFICIAL_LIVE, SOURCE_TIER_OFFICIAL_ARCHIVED}]
    user = [c for c in candidates if c.get("source_tier") == SOURCE_TIER_USER_PROVIDED]

    if official:
        candidates = official
    elif user:
        candidates = user

    candidates.sort(
        key=lambda c: (
            c.get("source_tier") == SOURCE_TIER_OFFICIAL_LIVE,
            c.get("source_tier") == SOURCE_TIER_OFFICIAL_ARCHIVED,
            float(c.get("confidence", 0.0)),
            str(c.get("source_url") or ""),
        ),
        reverse=True,
    )
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
        raw = [dict(item) for item in (_SEARCH_PROVIDER(command_text, role, state) or []) if isinstance(item, dict)]
    except Exception:
        return []
    return _filter_and_rank_provider_results(command_text, role, raw)


# ---------------------------------------------------------------------------
# Hermes To-line candidate routing hook (L.31X-1)
# ---------------------------------------------------------------------------
def _module_ready_for_to_patch(module: ModuleType) -> bool:
    required = (
        "_maybe_add_source_candidate",
        "_SOURCE_BACKED_LOOKUP_ADAPTER",
        "_is_controlled_alias",
        "_UNIT_ALIASES",
        "_candidate_id",
        "_ensure_cands",
        "_clean",
    )
    return all(hasattr(module, name) for name in required)


def _is_controlled_in_hermes(module: ModuleType, text: str) -> bool:
    try:
        if module._is_controlled_alias(text):  # type: ignore[attr-defined]
            return True
    except Exception:
        pass
    aliases = getattr(module, "_UNIT_ALIASES", {})
    return isinstance(aliases, dict) and _dict_values_match(text, aliases)


def _strip_to_letterhead(resolved: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(resolved)
    for key in ("letterhead_top_line", "letterhead_activity", "letterhead_address", "unit_identity"):
        cleaned.pop(key, None)
    return {k: v for k, v in cleaned.items() if v}


def install_hermes_to_line_candidate_patch(module: ModuleType | None = None) -> bool:
    """Patch Hermes candidate routing so unresolved To fields may create candidates."""

    candidates: list[ModuleType] = []
    if module is not None:
        candidates.append(module)
    for name in ("hermes_chat_builder", "__main__"):
        found = sys.modules.get(name)
        if isinstance(found, ModuleType) and found not in candidates:
            candidates.append(found)

    for target in candidates:
        if getattr(target, "_OFFICIAL_LOOKUP_TO_LINE_PATCHED", False):
            return True
        if not _module_ready_for_to_patch(target):
            continue

        original = target._maybe_add_source_candidate  # type: ignore[attr-defined]

        def _maybe_add_source_candidate_with_to(
            state: dict[str, Any],
            fields: dict[str, str],
            *,
            _original: Callable[[dict[str, Any], dict[str, str]], dict[str, Any] | None] = original,
            _target: ModuleType = target,
        ) -> dict[str, Any] | None:
            pending = _original(state, fields)
            if pending:
                return pending

            text = fields.get("to")
            adapter = getattr(_target, "_SOURCE_BACKED_LOOKUP_ADAPTER", None)
            if not text or adapter is None or _is_controlled_in_hermes(_target, text):
                return None

            try:
                res = adapter(text, "to", state)
            except Exception:
                return None
            if not isinstance(res, dict) or not isinstance(res.get("resolved_value"), dict):
                return None

            resolved = _strip_to_letterhead(dict(res.get("resolved_value") or {}))
            if not resolved.get("to"):
                return None

            cand = {
                "candidate_id": res.get("candidate_id")
                or _target._candidate_id("to", text, str(res.get("source_url") or "")),  # type: ignore[attr-defined]
                "candidate_type": res.get("candidate_type") or "command_expansion",
                "input_text": _target._clean(text),  # type: ignore[attr-defined]
                "field": "to",
                "resolved_value": resolved,
                "source_title": res.get("source_title") or "Source-backed command result",
                "source_url": str(res.get("source_url") or ""),
                "source_tier": res.get("source_tier") or "unresolved",
                "source_limitation": res.get("source_limitation")
                or "Candidate requires user confirmation before applying.",
                "confidence": res.get("confidence", 0),
                "requires_user_confirmation": True,
                "status": "pending",
            }
            cands = _target._ensure_cands(state)  # type: ignore[attr-defined]
            if any(c.get("candidate_id") == cand["candidate_id"] for c in cands["rejected"]):
                return None
            if not any(c.get("candidate_id") == cand["candidate_id"] for c in cands["pending"]):
                cands["pending"].append(cand)
            return cand

        target._maybe_add_source_candidate = _maybe_add_source_candidate_with_to  # type: ignore[attr-defined]
        target._OFFICIAL_LOOKUP_TO_LINE_PATCHED = True  # type: ignore[attr-defined]
        return True
    return False


def _install_hermes_to_line_candidate_patch_when_ready() -> None:
    for _ in range(2000):
        if install_hermes_to_line_candidate_patch():
            return
        time.sleep(0.001)


if os.getenv("SECNAV_DISABLE_HERMES_TO_LINE_PATCH", "").strip().lower() not in {"1", "true", "yes", "on"}:
    threading.Thread(target=_install_hermes_to_line_candidate_patch_when_ready, daemon=True).start()


# ---------------------------------------------------------------------------
# Public adapter
# ---------------------------------------------------------------------------
def official_command_lookup(
    command_text: str,
    role: str,
    state: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return an official-source command candidate or ``None``."""

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
