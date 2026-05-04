#!/usr/bin/env python
"""
v6 Body Structure Validator
Validate parsed body records against v6 structure rules.
"""

import json
import os
import sys


# Import the loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from body_v6_parse import detect_marker_level, main as parse_body


def validate_body(payload):
    """
    Validate body structure from a payload dict.
    Returns list of error strings (empty if valid).
    """
    body_records = []
    for idx, line in enumerate(payload.get("body", [])):
        level, marker, text = detect_marker_level(line)
        body_records.append({
            "raw": line,
            "level": level,
            "marker": marker,
            "text": text,
            "index": idx
        })
    
    # Validate
    errors = []
    
    # Check for skipped levels within nested structure
    # Track parent-child relationships
    prev_level = None
    for i, rec in enumerate(body_records):
        level = rec["level"]
        if level is not None:
            if prev_level is not None:
                # Can only go down by any amount, or up by 1
                if level > prev_level + 1:
                    errors.append(f"Skipped level(s): record {i} jumps from level {prev_level} to level {level}")
            prev_level = level
    
    # Sequence checks
    # Level 1: numeric markers should increment
    level1_records = [r for r in body_records if r["level"] == 1]
    if level1_records:
        for i, rec in enumerate(level1_records):
            expected_num = i + 1
            if rec["marker"]:
                try:
                    actual_num = int(rec["marker"].strip("."))
                    if actual_num != expected_num:
                        errors.append(f"Level 1 marker at index {rec['index']} is {rec['marker']}, expected {expected_num}.")
                except ValueError:
                    pass
    
    # Level 2: alpha markers should increment (a, b, c)
    level2_records = [r for r in body_records if r["level"] == 2]
    if level2_records:
        for i, rec in enumerate(level2_records):
            if rec["marker"]:
                try:
                    letter = rec["marker"].strip(".").lower()
                    expected_letter = chr(ord('a') + i)
                    if letter != expected_letter:
                        errors.append(f"Level 2 marker at index {rec['index']} is {rec['marker']}, expected {expected_letter}.")
                except ValueError:
                    pass
    
    # Level 3: numeric paren markers should increment
    level3_records = [r for r in body_records if r["level"] == 3]
    for i, rec in enumerate(level3_records):
        if rec["marker"]:
            try:
                actual_num = int(rec["marker"].strip("()"))
                expected_num = i + 1
                if actual_num != expected_num:
                    errors.append(f"Level 3 marker at index {rec['index']} is {rec['marker']}, expected ({expected_num}).")
            except ValueError:
                pass
    
    # Level 4: alpha paren markers should increment
    level4_records = [r for r in body_records if r["level"] == 4]
    for i, rec in enumerate(level4_records):
        if rec["marker"]:
            try:
                letter = rec["marker"].strip("()").lower()
                expected_letter = chr(ord('a') + i)
                if letter != expected_letter:
                    errors.append(f"Level 4 marker at index {rec['index']} is {rec['marker']}, expected ({expected_letter}).")
            except ValueError:
                pass
    
    # Minimum subdivision rule
    # If a parent has child items at the next level, it must have at least 2 child items
    # Track consecutive children under each parent
    parent_children = {}  # key: (parent_level, parent_marker), value: list of child records
    
    current_parent = None
    for i, rec in enumerate(body_records):
        level = rec["level"]
        if level is None:
            continue
        
        if level == 1:
            current_parent = (1, rec["marker"])
        elif level == 2:
            # Find the most recent level-1 parent
            for j in range(i - 1, -1, -1):
                if body_records[j]["level"] == 1:
                    current_parent = (1, body_records[j]["marker"])
                    break
        elif level == 3:
            # Find the most recent level-2 parent
            for j in range(i - 1, -1, -1):
                if body_records[j]["level"] == 2:
                    current_parent = (2, body_records[j]["marker"])
                    break
        elif level == 4:
            # Find the most recent level-3 parent
            for j in range(i - 1, -1, -1):
                if body_records[j]["level"] == 3:
                    current_parent = (3, body_records[j]["marker"])
                    break
        
        if current_parent:
            if current_parent not in parent_children:
                parent_children[current_parent] = []
            if level > current_parent[0]:  # This is a child of current_parent
                parent_children[current_parent].append(rec)
    
    # Check each parent has at least 2 children if it has any
    for parent_key, children in parent_children.items():
        if len(children) == 1:
            errors.append(f"Parent {parent_key[1]} at level {parent_key[0]} has only 1 child at level {parent_key[0] + 1}; minimum 2 required")
    
    return errors


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Accept optional file path argument
    if len(sys.argv) > 1:
        sample_path = os.path.join(base_dir, sys.argv[1])
    else:
        sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    
    if not os.path.exists(sample_path):
        print(f"Missing: {sample_path}")
        return
    
    # Load and parse payload
    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Validate
    errors = validate_body(payload)
    
    # Print results
    print("=== BODY VALIDATION ===")
    if errors:
        print("FAIL")
        for err in errors:
            print(f"<error>{err}</error>")
    else:
        print("PASS")


if __name__ == "__main__":
    main()
