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
from typing import Any, Callable, Iterable
from urllib.parse import urlparse


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
# Source filter and ranking helpers (L.32D)
# ---------------------------------------------------------------------------
# These helpers are the single deterministic place that classifies allowed /
# disallowed official source domains, source tiers, provenance completeness,
# confidence gates, and conflict-preserving ranking.  They operate only on
# supplied result dictionaries: no network, no filesystem, no static command
# database.  Domain allow/disallow lists are permitted; command databases are
# not.

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

OFFICIAL_LIVE_CONFIDENCE_THRESHOLD = 0.85
OFFICIAL_ARCHIVED_CONFIDENCE_THRESHOLD = 0.70

_TO_STRIP_KEYS: tuple[str, ...] = (
    "letterhead_top_line",
    "letterhead_activity",
    "letterhead_address",
    "unit_identity",
)

_TIER_PRIORITY: dict[str, int] = {
    SOURCE_TIER_OFFICIAL_LIVE: 0,
    SOURCE_TIER_OFFICIAL_ARCHIVED: 1,
    SOURCE_TIER_USER_PROVIDED: 2,
    SOURCE_TIER_SECONDARY_CREDIBLE: 3,
    SOURCE_TIER_UNRESOLVED: 4,
}


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _scheme(url: str) -> str:
    try:
        return urlparse(url).scheme.lower()
    except Exception:
        return ""


def normalize_source_url(url: str) -> str:
    """Normalize a source URL for deterministic comparison.

    Lowercases, strips surrounding whitespace, drops any fragment, and
    removes trailing slashes.  Returns ``""`` for empty/missing input.
    """
    text = (url or "").strip().lower()
    if not text:
        return ""
    text = text.split("#", 1)[0]
    return text.rstrip("/")


def is_allowed_official_source(url: str) -> bool:
    """Return True when *url* is an allowed official source domain.

    Allowed: any ``.mil`` host (covers navy.mil, marines.mil, usmc.mil,
    dod.mil and their subdomains) and ``defense.gov`` (and subdomains).
    Everything else — social media, news sites, commercial directories,
    unofficial base guides, pseudo-URLs, and empty/missing URLs — is
    disallowed as an official source.
    """
    host = _host(url)
    if not host:
        return False
    host = host.split(":", 1)[0]  # strip any port
    labels = [label for label in host.split(".") if label]
    if not labels:
        return False
    if labels[-1] == "mil":
        return True
    if len(labels) >= 2 and labels[-2] == "defense" and labels[-1] == "gov":
        return True
    return False


def classify_source_url(url: str) -> dict[str, Any]:
    """Classify a source URL into a deterministic descriptor dict.

    Returns keys: ``url`` (normalized), ``host``, ``scheme``, ``is_official``,
    ``is_pseudo_url``, and ``reason`` (empty when official).
    """
    normalized = normalize_source_url(url)
    host = _host(normalized)
    scheme = _scheme(normalized)
    is_pseudo = scheme in {"static", "localdb", "file", "data"} or normalized.startswith(
        ("static://", "localdb://")
    )
    is_official = is_allowed_official_source(normalized)
    if not normalized:
        reason = "missing_source_url"
    elif is_pseudo:
        reason = "pseudo_url"
    elif not is_official:
        reason = "non_official_domain"
    else:
        reason = ""
    return {
        "url": normalized,
        "host": host,
        "scheme": scheme,
        "is_official": is_official,
        "is_pseudo_url": is_pseudo,
        "reason": reason,
    }


def _result_tier(result: dict[str, Any]) -> str:
    tier = str(result.get("source_tier") or "").strip().lower()
    return tier if tier in _VALID_SOURCE_TIERS else SOURCE_TIER_UNRESOLVED


def _confidence(result: dict[str, Any]) -> float:
    try:
        value = float(result.get("confidence", 0.0))
    except Exception:
        value = 0.0
    return max(0.0, min(1.0, value))


def _has_complete_provenance(result: dict[str, Any]) -> bool:
    if not isinstance(result.get("resolved_value"), dict) or not result.get("resolved_value"):
        return False
    if not result.get("source_tier"):
        return False
    if not _clean(result.get("source_title")):
        return False
    if not _clean(result.get("source_url")):
        return False
    if result.get("confidence") is None:
        return False
    return True


def _archived_caution(result: dict[str, Any]) -> bool:
    limitation = _norm(result.get("source_limitation") or "")
    return "archiv" in limitation or "valid" in limitation


def _exact_command_match(result: dict[str, Any], norm_cmd: str) -> bool:
    if not norm_cmd:
        return False
    rv = result.get("resolved_value")
    if isinstance(rv, dict):
        for value in rv.values():
            if isinstance(value, str) and _norm(value) == norm_cmd:
                return True
    title = result.get("source_title")
    if isinstance(title, str) and _norm(title) == norm_cmd:
        return True
    return False


def _strip_for_role(result: dict[str, Any], role: str) -> dict[str, Any]:
    cleaned = dict(result)
    rv = cleaned.get("resolved_value")
    if isinstance(rv, dict):
        resolved = dict(rv)
        if _norm(role) == "to":
            for key in _TO_STRIP_KEYS:
                resolved.pop(key, None)
        resolved = {k: v for k, v in resolved.items() if v}
        cleaned["resolved_value"] = resolved
    return cleaned


def filter_provider_results(
    results: Iterable[dict[str, Any]],
    role: str,
) -> list[dict[str, Any]]:
    """Return apply-ready results from *results* for *role*.

    Deterministic and side-effect free.  Drops results that are not
    apply-ready: unresolved and secondary_credible tiers, official results
    missing provenance or confidence, disallowed source URLs, and archived
    results without a caution limitation.  For ``to``, letterhead and
    unit_identity fields are stripped from ``resolved_value``.
    """
    role_key = _norm(role)
    if role_key not in {"from", "to"}:
        return []
    out: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        result = _strip_for_role(item, role_key)
        rv = result.get("resolved_value")
        if not isinstance(rv, dict) or not rv.get(role_key):
            continue
        tier = _result_tier(result)
        if tier == SOURCE_TIER_OFFICIAL_LIVE:
            if not is_allowed_official_source(result.get("source_url")):
                continue
            if _confidence(result) < OFFICIAL_LIVE_CONFIDENCE_THRESHOLD:
                continue
            if not _has_complete_provenance(result):
                continue
            out.append(result)
        elif tier == SOURCE_TIER_OFFICIAL_ARCHIVED:
            if not is_allowed_official_source(result.get("source_url")):
                continue
            if not _has_complete_provenance(result):
                continue
            if _confidence(result) < OFFICIAL_ARCHIVED_CONFIDENCE_THRESHOLD:
                continue
            if not _archived_caution(result):
                continue
            out.append(result)
        elif tier == SOURCE_TIER_USER_PROVIDED:
            out.append(result)
        # secondary_credible and unresolved are not apply-ready
    return out


def rank_provider_results(
    results: Iterable[dict[str, Any]],
    role: str,
    command_text: str = "",
) -> list[dict[str, Any]]:
    """Sort *results* deterministically by tier, confidence, match, then URL.

    Ordering keys, in priority order:

      1. source_tier priority (official_live < official_archived <
         user_provided < secondary_credible < unresolved)
      2. confidence descending
      3. exact normalized *command_text* match in resolved value or title
      4. normalized source_url alphabetical (stable tie-breaker)

    Conflicts on resolved From/To values are preserved — this helper never
    collapses or selects a single result.
    """
    role_key = _norm(role)
    norm_cmd = _norm(command_text)
    items = [_strip_for_role(item, role_key) for item in results if isinstance(item, dict)]

    def key(result: dict[str, Any]) -> tuple[int, float, int, str]:
        priority = _TIER_PRIORITY.get(_result_tier(result), 99)
        confidence = _confidence(result)
        match = 1 if _exact_command_match(result, norm_cmd) else 0
        url = normalize_source_url(result.get("source_url") or "")
        return (priority, -confidence, -match, url)

    return sorted(items, key=key)


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


# ---------------------------------------------------------------------------
# Live retrieval skeleton (L.32F)
# ---------------------------------------------------------------------------
class OfficialCommandRetrievalError(OfficialCommandProviderError):
    """Base exception for official command live retrieval failures."""


class OfficialCommandRetrievalTimeout(OfficialCommandRetrievalError, TimeoutError):
    """Raised by injected fetchers when a retrieval attempt times out."""


OfficialCommandRetrievalResult = dict[str, Any]
OfficialCommandFetcher = Callable[[str, float], str]
OfficialCommandParser = Callable[[str, str, str, str], Iterable[dict[str, Any]]]

DEFAULT_OFFICIAL_LOOKUP_TIMEOUT_SECONDS = 3.0
MAX_OFFICIAL_LOOKUP_TIMEOUT_SECONDS = 10.0
_STATE_FIXTURE_URLS_KEY = "_official_lookup_fixture_urls"


def clamp_official_lookup_timeout(timeout_seconds: Any = None) -> float:
    """Return a bounded lookup timeout.

    Invalid, missing, zero, or negative values fall back to the default.
    Values above the maximum are clamped to the maximum.
    """
    try:
        value = float(timeout_seconds)
    except Exception:
        value = DEFAULT_OFFICIAL_LOOKUP_TIMEOUT_SECONDS
    if value <= 0:
        value = DEFAULT_OFFICIAL_LOOKUP_TIMEOUT_SECONDS
    return min(value, MAX_OFFICIAL_LOOKUP_TIMEOUT_SECONDS)


def discover_candidate_urls(
    command_text: str,
    role: str,
    state: dict[str, Any] | None = None,
    *,
    candidate_urls: Iterable[str] | None = None,
) -> list[str]:
    """Return deterministic candidate URLs for the live retriever skeleton.

    This placeholder performs no web search and contains no command database.
    It returns explicit constructor-supplied URLs first; when none are supplied,
    tests may provide URLs in ``state['_official_lookup_fixture_urls']``.
    """
    urls: list[str] = []
    if candidate_urls is not None:
        urls.extend(str(url) for url in candidate_urls if str(url or "").strip())
    elif isinstance(state, dict):
        fixture_urls = state.get(_STATE_FIXTURE_URLS_KEY)
        if isinstance(fixture_urls, (list, tuple)):
            urls.extend(str(url) for url in fixture_urls if str(url or "").strip())
    return urls


def parse_official_source_page(
    command_text: str,
    role: str,
    url: str,
    page_text: str,
) -> list[dict[str, Any]]:
    """Default parser placeholder for official source pages.

    The default parser intentionally returns ``[]``.  Future phases may replace
    it with source-specific parsing, but this skeleton never invents command
    names, sources, or letterhead from page text.
    """
    return []


class OfficialCommandLiveRetriever(OfficialCommandProvider):
    """Disabled-by-default live retrieval boundary for official lookup.

    This class combines deterministic URL discovery, allowed-domain precheck,
    an injectable fetch abstraction, and an injectable parser.  It never reads
    the adapter enable gate, never registers itself, never mutates state, and
    performs no network activity unless constructed with ``enable_network=True``
    and an explicit fetcher.
    """

    def __init__(
        self,
        *,
        enable_network: bool = False,
        candidate_urls: Iterable[str] | None = None,
        fetcher: OfficialCommandFetcher | None = None,
        parser: OfficialCommandParser | None = None,
        timeout_seconds: Any = None,
    ) -> None:
        self.enable_network = bool(enable_network)
        self._candidate_urls = list(candidate_urls or [])
        self._fetcher = fetcher
        self._parser = parser or parse_official_source_page
        self.timeout_seconds = clamp_official_lookup_timeout(timeout_seconds)

    def search(
        self,
        command_text: str,
        role: str,
        state: dict[str, Any],
    ) -> Iterable[dict[str, Any]]:
        """Return raw provider result dictionaries or ``[]`` fail-closed."""
        role_key = _norm(role)
        if role_key not in {"from", "to"}:
            return []
        if not _norm(command_text):
            return []
        if not self.enable_network or self._fetcher is None:
            return []

        results: list[dict[str, Any]] = []
        urls = discover_candidate_urls(
            command_text,
            role_key,
            state,
            candidate_urls=self._candidate_urls if self._candidate_urls else None,
        )
        for url in urls:
            if not is_allowed_official_source(url):
                continue
            try:
                page_text = self._fetcher(url, self.timeout_seconds)
            except (OfficialCommandRetrievalTimeout, TimeoutError):
                continue
            except Exception:
                continue
            if not page_text:
                continue
            try:
                parsed = self._parser(command_text, role_key, url, page_text)
            except Exception:
                continue
            for item in parsed or []:
                if isinstance(item, dict):
                    results.append(dict(item))
        return results

    def __call__(
        self,
        command_text: str,
        role: str,
        state: dict[str, Any],
    ) -> Iterable[dict[str, Any]]:
        return self.search(command_text, role, state)


def build_live_retriever(
    *,
    enable_network: bool = False,
    candidate_urls: Iterable[str] | None = None,
    fetcher: OfficialCommandFetcher | None = None,
    parser: OfficialCommandParser | None = None,
    timeout_seconds: Any = None,
) -> OfficialCommandLiveRetriever:
    """Build a disabled-by-default live retriever skeleton.

    The returned object is not registered with the adapter automatically.
    """
    return OfficialCommandLiveRetriever(
        enable_network=enable_network,
        candidate_urls=candidate_urls,
        fetcher=fetcher,
        parser=parser,
        timeout_seconds=timeout_seconds,
    )


def build_live_provider(
    *,
    enable_network: bool = False,
    candidate_urls: Iterable[str] | None = None,
    fetcher: OfficialCommandFetcher | None = None,
    parser: OfficialCommandParser | None = None,
    timeout_seconds: Any = None,
) -> OfficialCommandLiveRetriever:
    """Build an OfficialCommandProvider-compatible live provider skeleton."""
    return build_live_retriever(
        enable_network=enable_network,
        candidate_urls=candidate_urls,
        fetcher=fetcher,
        parser=parser,
        timeout_seconds=timeout_seconds,
    )
