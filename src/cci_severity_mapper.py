#!/usr/bin/env python3
"""
CCI Severity Mapper — Shared config-driven severity resolution module.

Provides:
    effective_severity(rule_id, catalog_severity="error") -> str
        Returns one of: "advisory", "warning", "error".

Behavior:
    - Attempts to load config/cci_enforcement_config.json relative to repo root.
    - Missing / unreadable / malformed / unknown schema  safe advisory fallback.
    - Unknown rule ID  advisory fallback.
    - Rule not in allowlist  advisory fallback.
    - effective_severity > allow_override_up_to  clamped to ceiling.
    - Unsupported severity strings  advisory fallback.

Safe on all error paths. No external dependencies beyond stdlib.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

_VALID_SCHEMAS = frozenset(["CCI_ENFORCEMENT_CONFIG_V1"])
_VALID_SEVERITIES = frozenset(["advisory", "warning", "error"])
_DEFAULT_SEVERITY = "advisory"
_CONFIG_FILENAME = "cci_enforcement_config.json"

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _repo_root() -> Path:
    """Return the repository root directory (where src/ lives)."""
    # This file lives in src/; go up one level.
    return Path(__file__).resolve().parents[1]


def _load_config(path: Path) -> dict[str, Any] | None:
    """Load and parse the config JSON file. Return None on any failure."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _resolve_severity(
    rule_id: str,
    catalog_severity: str,
    config: dict[str, Any] | None,
) -> str:
    """Resolve effective severity for rule_id using config."""
    if config is None:
        return _DEFAULT_SEVERITY

    schema = config.get("_schema_version")
    if schema not in _VALID_SCHEMAS:
        return _DEFAULT_SEVERITY

    allowlist = config.get("_allowlist", [])
    if not isinstance(allowlist, list) or rule_id not in allowlist:
        return _DEFAULT_SEVERITY

    overrides = config.get("overrides", {})
    if not isinstance(overrides, dict):
        return _DEFAULT_SEVERITY

    override = overrides.get(rule_id)
    if not isinstance(override, dict):
        # Rule allowlisted but no override entry  use global_default
        global_default = config.get("global_default", _DEFAULT_SEVERITY)
        if global_default in _VALID_SEVERITIES:
            return _clamp(global_default, catalog_severity)
        return _DEFAULT_SEVERITY

    eff = override.get("effective_severity")
    if eff not in _VALID_SEVERITIES:
        return _DEFAULT_SEVERITY

    ceiling = override.get("allow_override_up_to")
    if ceiling not in _VALID_SEVERITIES:
        # If ceiling is invalid, fall back to advisory rather than trust unsafe config.
        return _DEFAULT_SEVERITY

    # Clamp effective_severity to ceiling and to catalog_severity
    eff = _clamp(eff, ceiling)
    eff = _clamp(eff, catalog_severity)
    return eff


def _clamp(severity: str, ceiling: str) -> str:
    """Clamp severity to not exceed ceiling."""
    order = {"advisory": 0, "warning": 1, "error": 2}
    s_val = order.get(severity, 0)
    c_val = order.get(ceiling, 2)
    if s_val > c_val:
        # Return the ceiling level
        for name, val in order.items():
            if val == c_val:
                return name
    return severity


# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------

def effective_severity(rule_id: str, catalog_severity: str = "error") -> str:
    """Return the effective severity for rule_id.

    Reads config from disk on every call (no caching) so temporary config
    changes or file replacements take effect immediately without restart.

    Args:
        rule_id: The rule identifier (e.g., "CCI-ROUTE-010").
        catalog_severity: The catalog-defined severity ceiling for this rule.
            Defaults to "error".

    Returns:
        One of "advisory", "warning", "error".
    """
    config_path = _repo_root() / "config" / _CONFIG_FILENAME
    config = _load_config(config_path)
    return _resolve_severity(rule_id, catalog_severity, config)


def reload_config() -> None:
    """No-op for API compatibility; config is re-read every call."""
    pass


def current_config_path() -> Path:
    """Return the canonical config path."""
    return _repo_root() / "config" / _CONFIG_FILENAME


# -------------------------------------------------------------------------
# CLI self-test
# -------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    rule_id = argv[1] if len(argv) > 1 else "CCI-ROUTE-010"
    catalog = argv[2] if len(argv) > 2 else "error"
    sev = effective_severity(rule_id, catalog)
    print(f"effective_severity({rule_id!r}, catalog={catalog!r}) = {sev!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
