"""
SECNAV M-5216.5 Letter Generator - ILM Validator
Validates ILM letter structures using YAML rule files from rules_db.

Input model:
- ILM structure as a dict with top-level key:
  sections: list of section objects
- each section object has:
  type, present, required, content

Validation pipeline:
1. structural validation (code invariants)
2. compliance validation (accepted + promoted provisional)
3. advisory checks (heuristic + non-promoted provisional warnings)
4. format resolution (stub)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


REQUIRED_SECTION_TYPES = [
    "metadata",
    "header",
    "references",
    "body",
    "closing",
    "administrative",
]


SECTION_OBJECT_REQUIRED_KEYS = [
    "type",
    "present",
    "required",
    "content",
]


ARRAY_CONTAINER_FIELDS = {
    ("references", "references"),
    ("references", "enclosures"),
    ("body", "paragraphs"),
    ("body", "cc"),
    ("closing", "copy_list"),
}


class RuleLoaderError(Exception):
    """Raised when rule files cannot be loaded or are malformed."""


class ValidationError(Exception):
    """Raised for invalid validator inputs."""


class RuleLoader:
    """Loads validation rules from YAML files in rules_db."""

    def __init__(self, rules_db_path: Optional[str] = None) -> None:
        base_dir = Path(__file__).resolve().parent
        self.rules_db_path = Path(rules_db_path) if rules_db_path else base_dir / "rules_db"

    def load_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        rule_files = {
            "accepted": self.rules_db_path / "accepted.yaml",
            "provisional": self.rules_db_path / "provisional.yaml",
            "heuristic": self.rules_db_path / "advisory.yaml",
        }

        loaded: Dict[str, List[Dict[str, Any]]] = {
            "accepted": [],
            "provisional": [],
            "heuristic": [],
        }

        for bucket, path in rule_files.items():
            if not path.exists():
                raise RuleLoaderError(f"Rule file not found: {path}")

            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}

            rules = data.get("rules")
            if not isinstance(rules, list):
                raise RuleLoaderError(f"Rule file must contain a 'rules' list: {path}")

            for index, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    raise RuleLoaderError(f"Rule at index {index} in {path} must be a mapping")
                self._validate_rule_shape(rule, path, index)
                loaded[bucket].append(rule)

        return loaded

    def _validate_rule_shape(self, rule: Dict[str, Any], path: Path, index: int) -> None:
        required_keys = [
            "rule_id",
            "status",
            "section",
            "field",
            "check_type",
            "params",
            "message",
            "source",
        ]
        missing = [key for key in required_keys if key not in rule]
        if missing:
            raise RuleLoaderError(
                f"Rule at index {index} in {path} missing keys: {', '.join(missing)}"
            )

        if not isinstance(rule["params"], dict):
            raise RuleLoaderError(
                f"Rule '{rule.get('rule_id')}' in {path} has non-mapping params"
            )


class ILMValidator:
    """Validates ILM structures using rules loaded from YAML."""

    def __init__(
        self,
        rules_db_path: Optional[str] = None,
        promoted_provisional: Optional[Iterable[str]] = None,
    ) -> None:
        self.rule_loader = RuleLoader(rules_db_path)
        self.rules = self.rule_loader.load_rules()
        self.promoted_provisional = set(promoted_provisional or [])

    def validate(self, ilm_input: Any) -> Dict[str, Any]:
        ilm = self._normalize_input(ilm_input)

        results = {
            "structural_passed": True,
            "compliance_passed": True,
            "errors": [],
            "warnings": [],
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

        self._validate_structure(ilm, results)

        if results["structural_passed"]:
            self._validate_compliance(ilm, results)

        self._validate_advisory(ilm, results)
        self.resolve_format_params(ilm)

        return results

    def _normalize_input(self, ilm_input: Any) -> Dict[str, Any]:
        if isinstance(ilm_input, str):
            try:
                ilm_input = json.loads(ilm_input)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Invalid JSON input: {exc}") from exc

        if not isinstance(ilm_input, dict):
            raise ValidationError("ILM input must be a dict or JSON object string")

        return ilm_input

    def _validate_structure(self, ilm: Dict[str, Any], results: Dict[str, Any]) -> None:
        sections = ilm.get("sections")
        if not isinstance(sections, list):
            self._add_issue(
                results,
                bucket="errors",
                rule_id="STRUCT-SECTIONS-REQUIRED",
                status="accepted",
                message="ILM must contain a 'sections' array",
                location="/sections",
            )
            results["structural_passed"] = False
            results["compliance_passed"] = False
            return

        section_map = self._build_section_map(sections, results)

        for section_type in REQUIRED_SECTION_TYPES:
            if section_type not in section_map:
                self._add_issue(
                    results,
                    bucket="errors",
                    rule_id="STRUCT-SECTION-REQUIRED",
                    status="accepted",
                    message=f"Required section '{section_type}' is missing",
                    location=f"/sections/{section_type}",
                )
                results["structural_passed"] = False
                results["compliance_passed"] = False
                continue

            section_obj = section_map[section_type]
            if section_obj.get("required") is True and section_obj.get("present") is not True:
                self._add_issue(
                    results,
                    bucket="errors",
                    rule_id="STRUCT-SECTION-PRESENT",
                    status="accepted",
                    message=f"Required section '{section_type}' must be marked present",
                    location=self._section_location(section_type),
                )
                results["structural_passed"] = False
                results["compliance_passed"] = False

            content = section_obj.get("content")
            if not isinstance(content, dict):
                self._add_issue(
                    results,
                    bucket="errors",
                    rule_id="STRUCT-SECTION-CONTENT",
                    status="accepted",
                    message=f"Section '{section_type}' content must be an object",
                    location=f"{self._section_location(section_type)}/content",
                )
                results["structural_passed"] = False
                results["compliance_passed"] = False
                continue

        for section_type, field in ARRAY_CONTAINER_FIELDS:
            section_obj = section_map.get(section_type)
            if not section_obj or not isinstance(section_obj.get("content"), dict):
                continue

            content = section_obj["content"]
            if field in content and not isinstance(content[field], list):
                self._add_issue(
                    results,
                    bucket="errors",
                    rule_id="STRUCT-FIELD-TYPE",
                    status="accepted",
                    message=f"Field '{field}' in section '{section_type}' must be an array",
                    location=f"{self._section_location(section_type)}/content/{field}",
                )
                results["structural_passed"] = False
                results["compliance_passed"] = False

    def _build_section_map(
        self,
        sections: List[Any],
        results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        section_map: Dict[str, Dict[str, Any]] = {}

        for index, section in enumerate(sections):
            location = f"/sections/{index}"

            if not isinstance(section, dict):
                if results is not None:
                    self._add_issue(
                        results,
                        bucket="errors",
                        rule_id="STRUCT-SECTION-OBJECT",
                        status="accepted",
                        message="Each section must be an object",
                        location=location,
                    )
                    results["structural_passed"] = False
                    results["compliance_passed"] = False
                continue

            missing = [key for key in SECTION_OBJECT_REQUIRED_KEYS if key not in section]
            if missing:
                if results is not None:
                    self._add_issue(
                        results,
                        bucket="errors",
                        rule_id="STRUCT-SECTION-KEYS",
                        status="accepted",
                        message=(
                            f"Section is missing required keys: {', '.join(missing)}"
                        ),
                        location=location,
                    )
                    results["structural_passed"] = False
                    results["compliance_passed"] = False
                continue

            section_type = section.get("type")
            if not isinstance(section_type, str) or section_type.strip() == "":
                if results is not None:
                    self._add_issue(
                        results,
                        bucket="errors",
                        rule_id="STRUCT-SECTION-TYPE",
                        status="accepted",
                        message="Section type must be a non-empty string",
                        location=f"{location}/type",
                    )
                    results["structural_passed"] = False
                    results["compliance_passed"] = False
                continue

            if not isinstance(section.get("present"), bool):
                if results is not None:
                    self._add_issue(
                        results,
                        bucket="errors",
                        rule_id="STRUCT-SECTION-PRESENT-TYPE",
                        status="accepted",
                        message="Section 'present' must be a boolean",
                        location=f"{location}/present",
                    )
                    results["structural_passed"] = False
                    results["compliance_passed"] = False

            if not isinstance(section.get("required"), bool):
                if results is not None:
                    self._add_issue(
                        results,
                        bucket="errors",
                        rule_id="STRUCT-SECTION-REQUIRED-TYPE",
                        status="accepted",
                        message="Section 'required' must be a boolean",
                        location=f"{location}/required",
                    )
                    results["structural_passed"] = False
                    results["compliance_passed"] = False

            if section_type not in section_map:
                section_map[section_type] = section
            else:
                if results is not None:
                    self._add_issue(
                        results,
                        bucket="errors",
                        rule_id="STRUCT-SECTION-DUPLICATE",
                        status="accepted",
                        message=f"Duplicate section type '{section_type}'",
                        location=location,
                    )
                    results["structural_passed"] = False
                    results["compliance_passed"] = False

        return section_map

    def _validate_compliance(self, ilm: Dict[str, Any], results: Dict[str, Any]) -> None:
        for rule in self.rules["accepted"]:
            self._apply_rule(ilm, rule, results, as_error=True)

        for rule in self.rules["provisional"]:
            if rule["rule_id"] in self.promoted_provisional:
                self._apply_rule(ilm, rule, results, as_error=True)

    def _validate_advisory(self, ilm: Dict[str, Any], results: Dict[str, Any]) -> None:
        for rule in self.rules["heuristic"]:
            self._apply_rule(ilm, rule, results, as_error=False)

        for rule in self.rules["provisional"]:
            if rule["rule_id"] not in self.promoted_provisional:
                self._apply_rule(ilm, rule, results, as_error=False)

    def _apply_rule(
        self,
        ilm: Dict[str, Any],
        rule: Dict[str, Any],
        results: Dict[str, Any],
        as_error: bool,
    ) -> None:
        status = str(rule.get("status", "")).lower()
        if status in {"rejected", "deprecated"}:
            return

        targets = self._resolve_targets(ilm, rule["section"], rule["field"])
        passed = True
        failing_locations: List[str] = []

        for location, value in targets:
            if not self._check_value(value, rule["check_type"], rule.get("params", {})):
                passed = False
                failing_locations.append(location)

        if passed:
            return

        bucket = "errors" if as_error else "warnings"
        if as_error:
            results["compliance_passed"] = False

        for location in failing_locations:
            self._add_issue(
                results,
                bucket=bucket,
                rule_id=rule["rule_id"],
                status=status,
                message=rule["message"],
                location=location,
            )

    def _resolve_targets(
        self,
        ilm: Dict[str, Any],
        section_type: str,
        field_path: str,
    ) -> List[Tuple[str, Any]]:
        section = self._find_section_by_type(ilm, section_type)
        if section is None:
            return [(self._section_location(section_type), None)]

        content = section.get("content")
        if not isinstance(content, dict):
            return [(f"{self._section_location(section_type)}/content", None)]

        if field_path == "":
            return [(f"{self._section_location(section_type)}/content", content)]

        tokens = field_path.split(".")
        current: List[Tuple[str, Any]] = [(f"{self._section_location(section_type)}/content", content)]

        for token in tokens:
            next_items: List[Tuple[str, Any]] = []
            is_array = token.endswith("[]")
            key = token[:-2] if is_array else token

            for base_path, value in current:
                if not isinstance(value, dict) or key not in value:
                    next_items.append((f"{base_path}/{key}", None))
                    continue

                child = value[key]
                child_path = f"{base_path}/{key}"

                if is_array:
                    if not isinstance(child, list):
                        next_items.append((child_path, None))
                        continue
                    if not child:
                        next_items.append((child_path, []))
                        continue
                    for index, item in enumerate(child):
                        next_items.append((f"{child_path}/{index}", item))
                else:
                    next_items.append((child_path, child))

            current = next_items

        return current

    def _find_section_by_type(self, ilm: Dict[str, Any], section_type: str) -> Optional[Dict[str, Any]]:
        sections = ilm.get("sections")
        if not isinstance(sections, list):
            return None

        for section in sections:
            if isinstance(section, dict) and section.get("type") == section_type:
                return section

        return None

    def _section_location(self, section_type: str) -> str:
        return f"/sections/{section_type}"

    def _check_value(self, value: Any, check_type: str, params: Dict[str, Any]) -> bool:
        if check_type == "required":
            return self._check_required(value)

        if check_type == "required_array":
            return self._check_required_array(value, params)

        if check_type == "regex":
            return self._check_regex(value, params)

        if check_type == "forbidden_strings":
            return self._check_forbidden_strings(value, params)

        if check_type == "max_length":
            return self._check_max_length(value, params)

        if check_type == "range":
            return self._check_range(value, params)

        raise ValidationError(f"Unsupported check_type: {check_type}")

    def _check_required(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, list):
            return len(value) > 0
        return True

    def _check_required_array(self, value: Any, params: Dict[str, Any]) -> bool:
        min_items = int(params.get("min", 1))
        if not isinstance(value, list):
            return False
        return len(value) >= min_items

    def _check_regex(self, value: Any, params: Dict[str, Any]) -> bool:
        pattern = params.get("pattern")
        if not isinstance(pattern, str) or pattern == "":
            raise ValidationError("regex rule requires a non-empty 'pattern'")
        if not isinstance(value, str):
            return False
        return re.fullmatch(pattern, value) is not None

    def _check_forbidden_strings(self, value: Any, params: Dict[str, Any]) -> bool:
        forbidden = params.get("forbidden")
        if forbidden is None:
            forbidden = params.get("patterns")
        if not isinstance(forbidden, list):
            raise ValidationError("forbidden_strings rule requires 'forbidden' or 'patterns' list")

        if isinstance(value, list):
            return all(self._check_forbidden_strings(item, params) for item in value)

        if not isinstance(value, str):
            return True

        lowered = value.lower()
        for item in forbidden:
            if isinstance(item, str) and item.lower() in lowered:
                return False
        return True

    def _check_max_length(self, value: Any, params: Dict[str, Any]) -> bool:
        if isinstance(value, list):
            return all(self._check_max_length(item, params) for item in value)
        if not isinstance(value, str):
            return False
        max_length = int(params.get("max", 0))
        return len(value) <= max_length

    def _check_range(self, value: Any, params: Dict[str, Any]) -> bool:
        if "allowed" in params:
            allowed = params["allowed"]
            return value in allowed

        min_value = params.get("min")
        max_value = params.get("max")

        if isinstance(value, list):
            numeric_value = len(value)
        else:
            numeric_value = value

        if not isinstance(numeric_value, (int, float)):
            return False

        if min_value is not None and numeric_value < min_value:
            return False
        if max_value is not None and numeric_value > max_value:
            return False
        return True

    def _add_issue(
        self,
        results: Dict[str, Any],
        bucket: str,
        rule_id: str,
        status: str,
        message: str,
        location: str,
    ) -> None:
        results[bucket].append(
            {
                "rule_id": rule_id,
                "status": status,
                "message": message,
                "location": location,
            }
        )

    def resolve_format_params(self, ilm: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "paper": "letter",
            "orientation": "portrait",
            "renderer_ready": True,
        }


def validate_ilm(
    ilm_input: Any,
    promoted_provisional: Optional[Iterable[str]] = None,
    rules_db_path: Optional[str] = None,
) -> Dict[str, Any]:
    validator = ILMValidator(
        rules_db_path=rules_db_path,
        promoted_provisional=promoted_provisional,
    )
    return validator.validate(ilm_input)
