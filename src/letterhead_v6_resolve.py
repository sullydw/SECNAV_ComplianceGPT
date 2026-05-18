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
    """
    # Get unit identity
    unit_identity = payload.get("unit_identity", {})
    family = unit_identity.get("letterhead_family", "")
    
    if not family:
        return {"lines": [], "gap_below": "one_blank_line"}
    
    # Resolve lines based on family
    raw_lines = []
    
    if family == "LH_USMC_ACTIVITY":
        # Line 1: UNITED STATES MARINE CORPS (branch line)
        raw_lines.append("UNITED STATES MARINE CORPS")
        
        # Line 2: UNIT_OR_ACTIVITY_NAME
        line2 = unit_identity.get("UNIT_OR_ACTIVITY_NAME", "")
        if line2:
            raw_lines.append(line2)
        
        # Check for parent line suppression
        suppress_parent = unit_identity.get("SUPPRESS_PARENT_LINE", False)
        
        # Line 3: NEXT_ECHELON_OR_PARENT (only if present and not suppressed)
        if not suppress_parent:
            line3 = unit_identity.get("NEXT_ECHELON_OR_PARENT", "")
            if line3:
                raw_lines.append(line3)
        
        # Location line: INSTALLATION_OR_LOCATION + STATE + ZIP9
        location = unit_identity.get("INSTALLATION_OR_LOCATION", "")
        state = unit_identity.get("STATE", "")
        zip9 = unit_identity.get("ZIP9", "")
        if location or state or zip9:
            parts = [location, state, zip9]
            raw_lines.append(" ".join(p for p in parts if p))
        
        # Gap below letterhead
        gap_below = "one_blank_line"
    
    elif family == "LH_HQMC":
        # HQMC uses static top lines
        raw_lines.append("DEPARTMENT OF THE NAVY")
        raw_lines.append("HEADQUARTERS UNITED STATES MARINE CORPS")
        gap_below = "one_blank_line"
    
    elif family == "LH_NAVY_ACTIVITY":
        # Navy activity: DEPARTMENT OF THE NAVY as top line
        raw_lines.append("DEPARTMENT OF THE NAVY")
        
        # Line 2: UNIT_OR_ACTIVITY_NAME
        line2 = unit_identity.get("UNIT_OR_ACTIVITY_NAME", "")
        if line2:
            raw_lines.append(line2)
        
        # Line 3: INSTALLATION_OR_LOCATION + " " + STATE
        location = unit_identity.get("INSTALLATION_OR_LOCATION", "")
        state = unit_identity.get("STATE", "")
        if location or state:
            raw_lines.append(f"{location} {state}".strip())
        
        gap_below = "one_blank_line"
    
    else:
        gap_below = "one_blank_line"
    
    return {"lines": raw_lines, "gap_below": gap_below}


def main():
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
