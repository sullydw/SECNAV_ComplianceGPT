#!/usr/bin/env python
"""
v6 Rule Query Tool
Query rules by type, section, status, or enabled.
"""

import argparse
import csv
import json
import os
import sys


# Import the loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rules_v6_loader import load_lookup_tables, load_csv_rules


def main():
    parser = argparse.ArgumentParser(description="v6 Rule Query Tool")
    parser.add_argument("--type", help="Filter by type (e.g., LAY, BEH)")
    parser.add_argument("--section", help="Filter by section (e.g., SEC_VIA)")
    parser.add_argument("--status", help="Filter by status (e.g., ACT)")
    parser.add_argument("--enabled", help="Filter by enabled (true/false/True/False)")
    
    args = parser.parse_args()
    
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    rules_dir = os.path.join(base_dir, "rules_v6")
    authoring_dir = os.path.join(rules_dir, "authoring")
    
    lookup_path = os.path.join(rules_dir, "lookup_tables.json")
    
    source_rules_path = os.path.join(authoring_dir, "source_rules.csv")
    layout_rules_path = os.path.join(authoring_dir, "layout_rules.csv")
    behavior_rules_path = os.path.join(authoring_dir, "behavior_rules.csv")
    marker_rules_path = os.path.join(authoring_dir, "marker_rules.csv")
    body_rules_path = os.path.join(authoring_dir, "body_rules.csv")
    letterhead_rules_path = os.path.join(authoring_dir, "letterhead_rules.csv")
    
    # Load lookup tables
    if not os.path.exists(lookup_path):
        print(f"Missing: {lookup_path}")
        sys.exit(1)
    lookup = load_lookup_tables(lookup_path)
    
    # Load all CSV rules
    csv_files = [
        (source_rules_path, "source_rules"),
        (layout_rules_path, "layout_rules"),
        (behavior_rules_path, "behavior_rules"),
        (marker_rules_path, "marker_rules"),
        (body_rules_path, "body_rules"),
        (letterhead_rules_path, "letterhead_rules")
    ]
    
    all_rules = []
    for path, _ in csv_files:
        if not os.path.exists(path):
            continue
        rules = load_csv_rules(path)
        all_rules.extend(rules)
    
    # Apply filters
    matched = []
    for row in all_rules:
        # Filter by type
        if args.type and row.get("type") != args.type:
            continue
        # Filter by section
        if args.section and row.get("sec") != args.section:
            continue
        # Filter by status
        if args.status and row.get("status") != args.status:
            continue
        # Filter by enabled
        if args.enabled:
            row_enabled = row.get("enabled", "").lower()
            if args.enabled.lower() not in [row_enabled, row_enabled]:
                continue
        matched.append(row)
    
    # Print results
    if not matched:
        print("No matching rules found.")
        return
    
    for row in matched:
        id_ = row.get("id", "")
        type_ = row.get("type", "")
        section = row.get("sec", "")
        action = row.get("action", "")
        target = row.get("target", "")
        condition = row.get("condition", "")
        notes = row.get("notes", "")
        family = row.get("family", "")
        
        if family:
            print(f"[{id_}] {type_} {family} {action} {target} {condition} {notes}")
        else:
            print(f"[{id_}] {type_} {section} {action} {target} {condition} {notes}")


if __name__ == "__main__":
    main()
