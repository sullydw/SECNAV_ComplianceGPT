#!/usr/bin/env python
"""
v6 Letterhead Resolver
Resolve letterhead lines based on family and unit identity.
"""

import csv
import json
import os
import sys


def load_csv_rules(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def resolve_letterhead(payload):
    """
    Resolve letterhead lines from payload.
    Returns dict with 'lines' (list) and 'gap_below' (str).

    Priority:
      1. unit_identity with letterhead_family (existing behavior)
      2. Fallback letterhead fields:
         - letterhead_top_line
         - letterhead_activity
         - letterhead_address
    """
    # Priority 1: unit identity
    unit_identity = payload.get("unit_identity", {})
    family = unit_identity.get("letterhead_family", "")

    if family:
        raw_lines = []
        if family == "LH_USMC_ACTIVITY":
            raw_lines.append("UNITED STATES MARINE CORPS")
            line2 = unit_identity.get("UNIT_OR_ACTIVITY_NAME", "")
            if line2:
                raw_lines.append(line2)
            suppress_parent = unit_identity.get("SUPPRESS_PARENT_LINE", False)
            if not suppress_parent:
                line3 = unit_identity.get("NEXT_ECHELON_OR_PARENT", "")
                if line3:
                    raw_lines.append(line3)
            location = unit_identity.get("INSTALLATION_OR_LOCATION", "")
            state = unit_identity.get("STATE", "")
            zip9 = unit_identity.get("ZIP9", "")
            if location or state or zip9:
                parts = [location, state, zip9]
                raw_lines.append(" ".join(p for p in parts if p))
            return {"lines": raw_lines, "gap_below": "one_blank_line"}

        elif family == "LH_HQMC":
            raw_lines.append("DEPARTMENT OF THE NAVY")
            raw_lines.append("HEADQUARTERS UNITED STATES MARINE CORPS")
            return {"lines": raw_lines, "gap_below": "one_blank_line"}

        elif family == "LH_NAVY_ACTIVITY":
            raw_lines.append("DEPARTMENT OF THE NAVY")
            line2 = unit_identity.get("UNIT_OR_ACTIVITY_NAME", "")
            if line2:
                raw_lines.append(line2)
            location = unit_identity.get("INSTALLATION_OR_LOCATION", "")
            state = unit_identity.get("STATE", "")
            if location or state:
                raw_lines.append(f"{location} {state}".strip())
            return {"lines": raw_lines, "gap_below": "one_blank_line"}

        else:
            return {"lines": raw_lines, "gap_below": "one_blank_line"}

    # Priority 2: fallback fields
    top = payload.get("letterhead_top_line", "")
    activity = payload.get("letterhead_activity", "")
    address = payload.get("letterhead_address", "")

    if top or activity or address:
        raw_lines = []
        if top:
            raw_lines.append(top)
        if activity:
            raw_lines.append(activity)
        if address:
            raw_lines.append(address)
        return {"lines": raw_lines, "gap_below": "one_blank_line"}

    # No letterhead data available
    return {"lines": [], "gap_below": "one_blank_line"}


def has_letterhead_data(payload) -> bool:
    """Return True if payload has sufficient letterhead data for a standard letter."""
    unit_identity = payload.get("unit_identity", {})
    if unit_identity.get("letterhead_family"):
        return True
    top = payload.get("letterhead_top_line", "")
    activity = payload.get("letterhead_activity", "")
    address = payload.get("letterhead_address", "")
    return bool(top and activity and address)


def resolve_letterhead_old(payload):
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    rules_dir = os.path.join(base_dir, "rules_v6")
    authoring_dir = os.path.join(rules_dir, "authoring")
    letterhead_rules_path = os.path.join(authoring_dir, "letterhead_rules.csv")
    
    # Load sample payload
    if not os.path.exists(sample_path):
        print(f"Missing: {sample_path}")
        return
    
    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Load letterhead rules
    if not os.path.exists(letterhead_rules_path):
        print(f"Missing: {letterhead_rules_path}")
        return
    
    letterhead_rules = load_csv_rules(letterhead_rules_path)
    
    # Get unit identity
    unit_identity = payload.get("unit_identity", {})
    family = unit_identity.get("letterhead_family", "")
    
    if not family:
        print("No letterhead_family specified in unit_identity")
        return
    
    # Resolve letterhead
    letterhead = resolve_letterhead(payload)
    letterhead_lines = letterhead.get("lines", [])
    gap_below = letterhead.get("gap_below", "one_blank_line")
    
    # Renumber lines sequentially for output
    resolved_lines = {}
    for i, line in enumerate(letterhead_lines, 1):
        resolved_lines[f"line_{i}"] = line
    resolved_lines["gap_below"] = gap_below
    
    # Print resolution
    print("=== LETTERHEAD RESOLUTION ===")
    print(f"family: {family}")
    for key in ["line_1", "line_2", "line_3", "gap_below"]:
        if key in resolved_lines:
            print(f"{key}: {resolved_lines[key]}")


if __name__ == "__main__":
    main()
